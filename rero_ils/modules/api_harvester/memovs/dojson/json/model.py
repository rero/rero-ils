# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Memovs json record transformation."""

import json
import re
from pathlib import Path

from flask import current_app
from iso639 import find as iso639_find
from requests.exceptions import RequestException

from rero_ils.modules.utils import get_mef_url, get_schema_for_resource, requests_retry_session

_IDREF_URL_RE = re.compile(r"idref\.fr/(\w+)")

# Maps RDA content type code (last segment of @id) to RERO-ILS document type
_CONTENT_TYPE_MAP = {
    # Audio
    "rdaco:1011": {"main_type": "docmaintype_audio", "subtype": "docsubtype_music"},  # performed music
    "rdaco:1012": {"main_type": "docmaintype_audio", "subtype": "docsubtype_sound"},  # sounds
    "rdaco:1013": {"main_type": "docmaintype_audio", "subtype": "docsubtype_recorded_words"},  # spoken word
    # Still image
    "rdaco:1014": {"main_type": "docmaintype_image", "subtype": "docsubtype_photography"},  # still image
    # Moving image
    "rdaco:1023": {
        "main_type": "docmaintype_movie_series",
        "subtype": "docsubtype_movie",
    },  # two-dimensional moving image
}

# Maps RDA content type code to the electronicLocator.content value used for
# the landingPage link back to the MemoVS record.
_LOCATOR_CONTENT_MAP = {
    "rdaco:1011": "audio",
    "rdaco:1012": "audio",
    "rdaco:1013": "audio",
    "rdaco:1014": "photography",
    "rdaco:1023": "film",
}


def normalize_newlines(value):
    """Normalise CRLF and CR line endings to LF in every string of a JSON structure.

    The Memovs source exports multi line free text (notes, summaries, …) with
    Windows line endings; they are kept as real line breaks in the ILS fields.

    :param value: source value (dict, list or scalar).
    :returns: the value with normalised line endings.
    """
    if isinstance(value, str):
        return value.replace("\r\n", "\n").replace("\r", "\n")
    if isinstance(value, dict):
        return {key: normalize_newlines(val) for key, val in value.items()}
    if isinstance(value, list):
        return [normalize_newlines(item) for item in value]
    return value


def to_marc_language(code):
    """Convert language code to MARC (ISO 639-2/B)."""
    try:
        return iso639_find(code)["iso639_2_b"]
    except Exception:
        return code


# Load valid codes from JSON schemas
_SCHEMA_DIR = Path(__file__).parents[4] / "documents/jsonschemas/documents"

with (_SCHEMA_DIR / "document_contribution_role-v0.0.1.json").open() as f:
    VALID_ROLES = set(json.load(f)["items"]["enum"])

with (_SCHEMA_DIR / "document_color_content-v0.0.1.json").open() as f:
    VALID_COLOR_CONTENT = set(json.load(f)["colorContent"]["items"]["enum"])

with (_SCHEMA_DIR / "document_production_method-v0.0.1.json").open() as f:
    VALID_PRODUCTION_METHODS = set(json.load(f)["productionMethod"]["items"]["enum"])

with (_SCHEMA_DIR / "document_content_media_carrier-v0.0.1.json").open() as f:
    _cmc_schema = json.load(f)
    VALID_CONTENT_TYPES = set(_cmc_schema["definitions"]["contentType"]["items"]["enum"])
    # Extract mediaType -> valid carrierTypes mapping from oneOf options
    VALID_MEDIA_TYPES = set()
    MEDIA_CARRIER_MAP = {}  # Maps mediaType to set of valid carrierTypes
    for option in _cmc_schema["contentMediaCarrier"]["items"]["oneOf"]:
        props = option.get("properties", {})
        if "mediaType" in props and (const := props["mediaType"].get("const")):
            VALID_MEDIA_TYPES.add(const)
            if "carrierType" in props and (enum := props["carrierType"].get("enum")):
                MEDIA_CARRIER_MAP[const] = set(enum)

with (_SCHEMA_DIR / "document_entity_local-v0.0.1.json").open() as f:
    VALID_ENTITY_TYPES = set(json.load(f)["properties"]["type"]["enum"])

with (_SCHEMA_DIR / "document_contribution_local-v0.0.1.json").open() as f:
    VALID_CONTRIBUTION_TYPES = set(json.load(f)["properties"]["type"]["enum"])

with (_SCHEMA_DIR / "document_provision_activity-v0.0.1.json").open() as f:
    VALID_PROVISION_TYPES = set(json.load(f)["provisionActivity"]["items"]["properties"]["type"]["enum"])

DEFAULT_PROVISION_TYPE = "bf:Publication"


class Transformation:
    """Transform a Memovs BIBFRAME/JSON-LD record into a RERO-ILS document dict."""

    def __init__(self, data=None, logger=None, verbose=False, transform=True):
        """Initialise the transformation.

        :param data: source Memovs record dict.
        :param logger: optional logger instance.
        :param verbose: enable verbose logging.
        :param transform: run all trans_* methods immediately when True.
        """
        self.data = data
        self.logger = logger
        self.verbose = verbose
        self.json_dict = {}
        self._iconographic_labels = []
        # Keyed by (entity_type, idref_id) → MEF $ref URL or None (miss cached too).
        self._mef_cache = {}
        # Reused across MEF lookups for HTTP keep-alive; lazily created on first use.
        self.session = None
        if data and transform:
            self._transform()

    def _transform(self):
        self.data = normalize_newlines(self.data)
        for func in dir(self):
            if func.startswith("trans_"):
                func = getattr(self, func)
                func()

    def do(self, data):
        """Transform a Memovs record dict and return the RERO-ILS document dict.

        :param data: source Memovs record dict.
        :returns: RERO-ILS document dict.
        """
        self.data = data
        self.json_dict = {}
        self._iconographic_labels = []
        self._transform()
        return self.json_dict

    @property
    def json(self):
        """Return the transformed dict, or None if empty."""
        return self.json_dict or None

    @property
    def memovs_id(self):
        """Extract the numeric ID from the record @id (e.g. 'urn:avn:41999' → '41999')."""
        if at_id := self.data.get("@id", ""):
            return at_id.split(":")[-1] if ":" in at_id else at_id
        return ""

    def _content_code(self):
        """Extract the RDA content type code from bf:content's @id.

        :returns: RDA content type code (e.g. "rdaco:1023"), or "" if absent.
        """
        content = self.data.get("bf:content", {})
        return content.get("@id", "").split("/")[-1]

    def trans_constants(self):
        """Set fixed required fields and determine document type from the RDA content type code.

        Falls back to docmaintype_other when the code is absent or unrecognised.
        """
        self.json_dict["$schema"] = get_schema_for_resource("doc")
        self.json_dict["harvested"] = True
        self.json_dict["issuance"] = {
            "main_type": "rdami:1001",
            "subtype": "materialUnit",
        }
        if "adminMetadata" not in self.json_dict:
            self.json_dict["adminMetadata"] = {}
        self.json_dict["adminMetadata"]["encodingLevel"] = "Not applicable"
        self.json_dict["fiction_statement"] = "unspecified"

        doc_type = _CONTENT_TYPE_MAP.get(self._content_code(), {"main_type": "docmaintype_other"})
        self.json_dict["type"] = [doc_type]

    def trans_pid(self):
        """Set pid to '(MEMOVS){id}' using the last segment of the record @id."""
        if self.memovs_id:
            self.json_dict["pid"] = f"(MEMOVS){self.memovs_id}"

    def trans_identified_by(self):
        """Collect identifiers from the record @id and bf:identifier.

        Identifiers with bf:noteType "cote" are excluded: call numbers are
        imported into the item's call_number field only (see
        ApiMemovs._extract_call_number), never into the document's identifiedBy.
        """
        identified_by = []

        if self.memovs_id:
            identified_by.append(
                {
                    "source": "MEMOVS",
                    "type": "bf:Local",
                    "value": f"(MEMOVS){self.memovs_id}",
                }
            )

        if identifiers := self.data.get("bf:identifier", []):
            identified_by.extend(
                {
                    "source": (note_type.upper() if (note_type := identifier.get("bf:noteType", "")) else "MEMOVS"),
                    "type": "bf:Local",
                    "value": value,
                }
                for identifier in identifiers
                if (value := identifier.get("rdf:value", "")) and identifier.get("bf:noteType", "").upper() != "COTE"
            )

        if identified_by:
            self.json_dict["identifiedBy"] = identified_by

    def trans_title(self):
        """Map bf:title.rdfs:label to a bf:Title entry."""
        title = {"type": "bf:Title"}

        bf_title = self.data.get("bf:title", {})
        if maintitle := bf_title.get("bf:mainTitle", ""):
            title["mainTitle"] = [{"value": maintitle}]
        if subtitle := bf_title.get("bf:subtitle", ""):
            title["subtitle"] = [{"value": subtitle}]

        self.json_dict["title"] = [title]

        if parallel := bf_title.get("bf:parallelTitle", {}):
            if parallel_title := parallel.get("bf:mainTitle", ""):
                self.json_dict["title"].append({"type": "bf:ParallelTitle", "mainTitle": [{"value": parallel_title}]})

    def _extract_idref_id(self, uri):
        """Extract IdRef identifier from a URI.

        :param uri: URI potentially containing an IdRef identifier.
        :returns: IdRef identifier string, or empty string if not found.
        """
        if match := _IDREF_URL_RE.search(uri):
            return match[1]
        return ""

    def _get_mef_ref(self, entity_type, idref_id):
        """Resolve an IdRef identifier against MEF and return the $ref URL.

        Results (including None for misses) are cached in ``_mef_cache`` so that
        entities shared across many records are only fetched once per process.

        :param entity_type: normalised BIBFRAME entity type (e.g. 'bf:Topic').
        :param idref_id: IdRef identifier.
        :returns: canonical MEF $ref URL, or None if not found.
        """
        cache_key = (entity_type, idref_id)
        if cache_key in self._mef_cache:
            return self._mef_cache[cache_key]

        entity_types = current_app.config.get("RERO_ILS_ENTITY_TYPES", {})
        mef_type = entity_types.get(entity_type, "concepts")
        base_url = get_mef_url(mef_type)
        if not base_url:
            self._mef_cache[cache_key] = None
            return None
        url = f"{base_url}/mef/latest/idref:{idref_id}"
        result = None
        if self.session is None:
            self.session = requests_retry_session()
        try:
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            if hits := data.get("hits", {}):
                item = (hits.get("hits") or [None])[0]
                data = item.get("metadata", {}) if item else {}
            else:
                data.pop("_created", None)
                data.pop("_updated", None)
            if pid := data.get("idref", {}).get("pid"):
                result = f"{base_url}/idref/{pid}"
        except (RequestException, KeyError, ValueError, TypeError, AttributeError) as err:
            current_app.logger.warning("MEF lookup failed for idref:%s: %s", idref_id, err)
        self._mef_cache[cache_key] = result
        return result

    def _resolve_entity(self, uri, entity_type, label):
        """Resolve an entity to a MEF $ref or a local authorized access point.

        Tries the IdRef URI first; falls back to a local entity when MEF lookup
        fails or no URI is present. When an IdRef ID is known but the entity is
        absent from MEF, the fallback entity carries an ``identifiedBy`` entry
        so the IdRef identifier is not lost.

        :param uri: @id URI of the entity (may contain an IdRef identifier).
        :param entity_type: normalised BIBFRAME entity type.
        :param label: rdfs:label used as fallback access point.
        :returns: entity dict, or None if neither MEF nor label is available.
        """
        if idref_id := self._extract_idref_id(uri):
            if mef_ref := self._get_mef_ref(entity_type, idref_id):
                return {"$ref": mef_ref}
            if label:
                return {
                    "authorized_access_point": label,
                    "type": entity_type,
                    "identifiedBy": {"type": "IdRef", "value": idref_id},
                }
            return None
        if label:
            return {"authorized_access_point": label, "type": entity_type}
        return None

    def _normalize_agent_type(self, agent_type):
        """Map bf:Organization to bf:Organisation to match the RERO-ILS schema spelling.

        :param agent_type: BIBFRAME agent type string.
        :returns: normalised agent type string.
        """
        return "bf:Organisation" if agent_type == "bf:Organization" else agent_type

    def trans_contribution(self):
        """Map bf:contribution entries to contribution dicts, resolving agents and roles.

        "bf:contribution":[
            {
                "bf:agent":{"@type":"bf:Person", "rdfs:label":"Binder, Pantaléon"},
                "bf:role":{"@id":"http://id.loc.gov/vocabulary/relators/pht"},
            },
            {
                "bf:agent":{"@type":"bf:Organisation", "rdfs:label":"Loterie Romande"},
                "bf:role":{"@id":"http://id.loc.gov/vocabulary/relators/spn", "rdfs:label":"Sponsor"},
            },
        ],

        Contributions whose role is "Sponsor" or "Partenaire" are excluded from
        import on request of the RERO+ business team.

        :returns: None; the result is stored in ``self.json_dict["contribution"]``.
        """
        contributions = []

        for contribution in self.data.get("bf:contribution", []):
            agent = contribution.get("bf:agent", {})
            agent_label = agent.get("rdfs:label", "")
            if agent_label.startswith(("http://", "https://")):
                current_app.logger.warning(
                    "Memovs %s: bf:contribution agent has a URL as rdfs:label (%s).",
                    self.memovs_id,
                    agent_label,
                )
                continue

            # Not importing "bf:role.rdfs:label"="Sponsor" ou "bf:role.rdfs:label"="Partenaire"
            if role := contribution.get("bf:role", {}):
                if role.get("rdfs:label", "") in ("Sponsor", "Partenaire"):
                    continue

            agent_type = agent.get("@type")
            normalized_type = self._normalize_agent_type(agent_type)

            if normalized_type not in VALID_CONTRIBUTION_TYPES:
                current_app.logger.warning(
                    "Invalid contribution type '%s' for memovs %s. Allowed types: %s. Skipping: %s",
                    agent_type,
                    self.memovs_id,
                    ", ".join(sorted(VALID_CONTRIBUTION_TYPES)),
                    agent_label,
                )
                continue

            role_code = "ctb"
            if (role_id := role.get("@id", "")) and "/" in role_id:
                code = role_id.split("/")[-1]
                if code in VALID_ROLES:
                    role_code = code
                else:
                    current_app.logger.warning(
                        "Unknown role '%s' for memovs %s, defaulting to 'ctb'.", code, self.memovs_id
                    )

            entity = self._resolve_entity(agent.get("@id", ""), normalized_type, agent_label)
            if entity is None:
                continue

            contributions.append({"role": [role_code], "entity": entity})

        if contributions:
            self.json_dict["contribution"] = contributions

    def trans_provision_activity(self):
        """Map the production year and agent from bf:provisionActivity.

        The year is read from bf:provisionActivity.startDate / bf:date. The
        dcterms dates are not used as a fallback: they tell when the Memovs
        record was created, not when the resource was produced. Without a
        resource date the unknown date stub is set, as provisionActivity is
        required by the schema.
        The agent statement reflects bf:provisionActivity.bf:agent only when
        the source actually exports one — no institution name is fabricated.
        """
        bf_provision = self.data.get("bf:provisionActivity", {})

        year = None
        date_info = bf_provision.get("bf:date", {})
        start_date = bf_provision.get("startDate", "")

        if start_date and (match := re.search(r"(\d{4})", str(start_date))):
            year = int(match[1])

        date_label = date_info.get("rdfs:label", "")
        if (
            not year
            and (date_value := date_info.get("rdf:value", ""))
            and (match := re.search(r"(\d{4})", str(date_value)))
        ):
            year = int(match[1])

        statement = []
        if place_label := bf_provision.get("bf:place", {}).get("rdfs:label", ""):
            statement.append({"label": [{"value": place_label}], "type": "bf:Place"})
        if agent := bf_provision.get("bf:agent", {}):
            if agent_label := agent.get("rdfs:label", ""):
                statement.append({"label": [{"value": agent_label}], "type": "bf:Agent"})

        provision_type = bf_provision.get("@type") or DEFAULT_PROVISION_TYPE
        if provision_type not in VALID_PROVISION_TYPES:
            current_app.logger.warning(
                "Invalid provisionActivity type '%s' for memovs %s, defaulting to '%s'.",
                provision_type,
                self.memovs_id,
                DEFAULT_PROVISION_TYPE,
            )
            provision_type = DEFAULT_PROVISION_TYPE
        provision_activity = {"type": provision_type}
        # a structured place (country) is only relevant for a publication
        if place_label and provision_type == "bf:Publication":
            # the source never exports a country code; default to "xx" (undetermined)
            provision_activity["place"] = [{"country": "xx"}]
        if year:
            statement.append({"label": [{"value": date_label or str(year)}], "type": "Date"})
            provision_activity["startDate"] = year
        else:
            provision_activity["startDate"] = 9999
            provision_activity["note"] = "Date(s) uncertain or unknown"
        if statement:
            provision_activity["statement"] = statement

        self.json_dict["provisionActivity"] = [provision_activity]

    def trans_electronic_locator(self):
        """Map thumbnail and landingPage locators to electronicLocator entries.

        thumbnail always maps to coverImage. landingPage's content reflects
        the RDA content type code (e.g. film, photography, audio), falling
        back to webSite when the code is absent or unrecognised.
        """
        electronic_locators = []

        if bf_elocs := self.data.get("bf:electronicLocator", []):
            for eloc in bf_elocs:
                url = eloc.get("@id", "")
                note_type = eloc.get("bf:noteType", "")

                if not url:
                    continue

                if note_type == "thumbnail":
                    locator = {"content": "coverImage", "type": "relatedResource", "url": url}
                    electronic_locators.append(locator)
                elif note_type == "landingPage":
                    content = _LOCATOR_CONTENT_MAP.get(self._content_code(), "webSite")
                    locator = {"content": content, "type": "relatedResource", "url": url}
                    electronic_locators.append(locator)

        if electronic_locators:
            self.json_dict["electronicLocator"] = electronic_locators

    def trans_language(self):
        """Map bf:language to MARC ISO 639-2/B codes; defaults to 'zxx' (no linguistic content) when absent."""
        languages = []
        for lang in self.data.get("bf:language", []):
            if value := lang.get("rdfs:label"):
                languages.append({"type": "bf:Language", "value": to_marc_language(value)})
        self.json_dict["language"] = languages or [{"type": "bf:Language", "value": "zxx"}]

    def trans_series_statement(self):
        """Build seriesStatement from bf:partOf (with optional noteType prefix) and bf:seriesStatement.

        bf:partOf entries of type "fonds" or "emission" are not series and are skipped.
        """
        series = []

        # bf:partOf entries may carry a noteType prefix (e.g. "Collection: Archives audiovisuelles")
        if bf_part_of := self.data.get("bf:partOf"):
            for item in bf_part_of:
                note_type = item.get("bf:noteType", "")
                if note_type.lower() in ("fonds", "emission"):
                    continue
                label = item.get("rdfs:label", "")
                if note_type and label:
                    title = f"{note_type}: {label}"
                elif label:
                    title = label
                else:
                    continue
                series.append({"seriesTitle": [{"value": title}]})

        if bf_series := self.data.get("bf:seriesStatement"):
            for item in bf_series:
                if item:
                    series.append({"seriesTitle": [{"value": item}]})

        if series:
            self.json_dict["seriesStatement"] = series

    def trans_subjects(self):
        """Map bf:subject entries to RERO-ILS subjects.

        Subjects with an IdRef identifier are linked to MEF; subjects without
        one are collected in ``_iconographic_labels`` and later written to a
        general ``note`` by :meth:`trans_summary`, so they stay searchable
        without appearing on the main detail view.
        """
        self._iconographic_labels = []
        subjects = []
        for item in self.data.get("bf:subject", []):
            if item:
                label = item.get("rdfs:label")
                item_type = item.get("@type")

                if not item_type:
                    current_app.logger.warning("Missing @type in entity for document %s: %s", self.memovs_id, item)
                    continue

                normalized_type = self._normalize_agent_type(item_type)
                if normalized_type not in VALID_ENTITY_TYPES:
                    current_app.logger.warning(
                        "Invalid entity type '%s' for memovs %s. Allowed types: %s. Skipping: %s",
                        item_type,
                        self.memovs_id,
                        ", ".join(sorted(VALID_ENTITY_TYPES)),
                        label,
                    )
                    continue

                if idref_id := self._extract_idref_id(item.get("@id", "")):
                    if mef_ref := self._get_mef_ref(normalized_type, idref_id):
                        subjects.append({"entity": {"$ref": mef_ref}})
                    elif label:
                        subjects.append(
                            {
                                "entity": {
                                    "type": normalized_type,
                                    "authorized_access_point": label,
                                    "identifiedBy": {"type": "IdRef", "value": idref_id},
                                }
                            }
                        )
                elif label:
                    self._iconographic_labels.append(label)

        if subjects:
            self.json_dict["subjects"] = subjects

    def trans_genre_form(self):
        """Map bf:genreForm entries of type bf:Topic to MEF-linked genreForm entries; other types are skipped."""
        if not (genre_form := self.data.get("bf:genreForm")):
            return
        genre_forms = []
        label = genre_form.get("rdfs:label")
        item_type = genre_form.get("@type")
        if item_type != "bf:Topic":
            current_app.logger.warning(
                "Invalid type '%s' in genreForm for memovs %s, only bf:Topic allowed. Skipping: %s",
                item_type,
                self.memovs_id,
                label,
            )
        elif idref_id := self._extract_idref_id(genre_form.get("@id", "")):
            if mef_ref := self._get_mef_ref("bf:Topic", idref_id):
                genre_forms.append({"entity": {"$ref": mef_ref}})
            elif label:
                genre_forms.append(
                    {
                        "entity": {
                            "type": "bf:Topic",
                            "authorized_access_point": label,
                            "identifiedBy": {"type": "IdRef", "value": idref_id},
                        }
                    }
                )
        if genre_forms:
            self.json_dict["genreForm"] = genre_forms

    def trans_summary(self):
        """Map bf:summary to summary.

        Subjects without an IdRef link (collected by trans_subjects into
        _iconographic_labels) go to a general note instead, so the tags stay
        searchable without appearing on the main detail view.
        """
        if description := self.data.get("bf:summary"):
            self.json_dict["summary"] = [{"label": [{"value": str(description)}]}]

        if iconographic_labels := self._iconographic_labels:
            self.json_dict.setdefault("note", []).append(
                {"noteType": "general", "label": ", ".join(iconographic_labels)}
            )

    def trans_table_of_contents(self):
        """Map bf:tableOfContents labels to a flat list of strings."""
        if not (bf_toc := self.data.get("bf:tableOfContents")):
            return
        entries = []
        for item in bf_toc:
            if label := item.get("rdfs:label", ""):
                entries.append(label)
        if entries:
            self.json_dict["tableOfContents"] = entries

    def trans_extent(self):
        """Map bf:extent (with dcterms:extent fallback) to extent and bf:duration to duration."""
        if bf_extent := self.data.get("bf:extent"):
            self.json_dict["extent"] = str(bf_extent)
        elif dcterms_extent := self.data.get("dcterms:extent"):
            self.json_dict["extent"] = str(dcterms_extent)

        if bf_duration := self.data.get("bf:duration"):
            self.json_dict["duration"] = [str(bf_duration)]

    def trans_notes(self):
        """Map source fields to document notes.

        - bf:soundCharacteristic → noteType ``otherPhysicalDetails``
        - bf:note labels (vsavmat, vsavgeo, vsavfonds) are written to a LocalField record by
          ApiMemovs.sync_local_field.
        """
        notes = []

        if sound := self.data.get("bf:soundCharacteristic"):
            if label := sound.get("rdfs:label"):
                notes.append({"noteType": "otherPhysicalDetails", "label": label})

        for note in self.data.get("bf:note", []):
            note_type = note.get("bf:noteType", "").lower()
            label = note.get("rdfs:label", "")
            if note_type == "general" and label:
                notes.append({"noteType": note_type, "label": label})

        if notes:
            self.json_dict["note"] = notes

    def trans_usage_and_access_policy(self):
        """Collect every label from bf:usageAndAccessPolicy (bf:rightsStatement is not imported)."""
        policies = []

        if usage := self.data.get("bf:usageAndAccessPolicy"):
            # Memovs sends a single dict; restricted-access documents may carry
            # a list of entries. Normalise to a list to handle both.
            items = usage if isinstance(usage, list) else [usage]
            for item in items:
                if label := item.get("rdfs:label", ""):
                    policies.append({"type": "bf:UsageAndAccessPolicy", "label": label})

        if policies:
            self.json_dict["usageAndAccessPolicy"] = policies

    def trans_color_content(self):
        """Map RDA color content codes from bf:colorContent, validating against the schema enum."""
        if not (color_content := self.data.get("bf:colorContent")):
            return

        colors = []
        for color in color_content:
            if color_id := color.get("@id", ""):
                code = color_id.split("/")[-1]
                if code in VALID_COLOR_CONTENT:
                    colors.append(code)

        if colors:
            self.json_dict["colorContent"] = list(dict.fromkeys(colors))

    def trans_production_method(self):
        """Map RDA production method codes from bf:productionMethod, validating against the schema enum."""
        if not (prod_method := self.data.get("bf:productionMethod")):
            return

        methods = []
        for method in prod_method:
            if method_id := method.get("@id", ""):
                code = method_id.split("/")[-1]
                if code in VALID_PRODUCTION_METHODS:
                    methods.append(code)

        if methods:
            self.json_dict["productionMethod"] = list(dict.fromkeys(methods))

    def trans_content_media_carrier(self):
        """Build contentMediaCarrier from bf:content, bf:media, and bf:carrier, validating each RDA code."""
        content_type = None
        if bf_content := self.data.get("bf:content"):
            if content_id := bf_content.get("@id", ""):
                code = content_id.split("/")[-1]
                if code in VALID_CONTENT_TYPES:
                    content_type = code
                else:
                    current_app.logger.warning(
                        "Invalid content type '%s' for memovs %s. Allowed types: %s",
                        code,
                        self.memovs_id,
                        ", ".join(sorted(VALID_CONTENT_TYPES)),
                    )

        media_type = None
        if bf_media := self.data.get("bf:media"):
            if media_id := bf_media.get("@id", ""):
                code = media_id.split("/")[-1]
                if code in VALID_MEDIA_TYPES:
                    media_type = code
                else:
                    current_app.logger.warning(
                        "Invalid media type '%s' for memovs %s. Allowed types: %s",
                        code,
                        self.memovs_id,
                        ", ".join(sorted(VALID_MEDIA_TYPES)),
                    )

        carrier_type = None
        if bf_carrier := self.data.get("bf:carrier"):
            if carrier_id := bf_carrier.get("@id", ""):
                code = carrier_id.split("/")[-1]
                if code == "rdact:1099":
                    code = "other"  # rdact:1099 is the IANA "other" code, mapped to the schema's "other" value
                if not media_type:
                    current_app.logger.warning(
                        "Carrier type '%s' provided without media type for memovs %s. "
                        "Carrier type requires a media type.",
                        code,
                        self.memovs_id,
                    )
                elif code in MEDIA_CARRIER_MAP.get(media_type, set()):
                    carrier_type = code
                else:
                    valid_carriers = MEDIA_CARRIER_MAP.get(media_type, set())
                    carriers_list = ", ".join(sorted(valid_carriers)) if valid_carriers else "none"
                    current_app.logger.warning(
                        "Invalid carrier type '%s' for media type '%s' in memovs %s. Allowed carrier types for %s: %s",
                        code,
                        media_type,
                        self.memovs_id,
                        media_type,
                        carriers_list,
                    )

        if content_type:
            cmc = {"contentType": [content_type]}
            if media_type:
                cmc["mediaType"] = media_type
                if carrier_type:
                    cmc["carrierType"] = carrier_type
            self.json_dict["contentMediaCarrier"] = [cmc]


memovs_json = Transformation()
