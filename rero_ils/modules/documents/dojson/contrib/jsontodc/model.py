# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""RERO ILS JSON to Dublin Core transformation rules.

See https://www.dublincore.org/specifications/dublin-core/dcmi-terms/.
"""

from dojson import Overdo, utils
from flask_babel import gettext as _

from rero_ils.modules.documents.extensions import TitleExtension
from rero_ils.modules.documents.serializers.base import CREATOR_ROLES
from rero_ils.modules.entities.models import EntityType
from rero_ils.modules.entities.remote_entities.utils import get_entity_localized_value


class DublinCoreOverdo(Overdo):
    """DoJSON Overdo converting RERO ILS documents to Dublin Core.

    :ivar language: target language for entity resolution and translations.
    :vartype language: str
    """

    def do(self, blob, ignore_missing=True, exception_handlers=None, language="fr"):
        """Transform RERO ILS JSON document to Dublin Core format.

        :param blob: RERO ILS document to transform.
        :type blob: dict
        :param ignore_missing: If False, raises MissingRule when a field has
            no transformation rule. Defaults to True.
        :type ignore_missing: bool, optional
        :param exception_handlers: Custom exception handlers for non-standard
            field processing. Defaults to None.
        :type exception_handlers: dict, optional
        :param language: Target language code for entity resolution and type
            translations. Affects which authorized access point is selected
            for multilingual entities. Defaults to "fr".
        :type language: str, optional
        :returns: the Dublin Core record.
        :rtype: dict
        :raises MissingRule: If ignore_missing=False and a field lacks a
            transformation rule.

        Example::

            converter = DublinCoreOverdo()
            rero_doc = {
                'pid': 'doc123',
                'title': [{
                    'type': 'bf:Title',
                    'mainTitle': [{'value': 'Sample Title'}],
                    'subtitle': [{'value': 'A Study'}]
                }],
                'responsibilityStatement': [[{'value': 'John Doe'}]],
                'contribution': [...],
                ...
            }
            dc_record = converter.do(rero_doc, language='en')
            dc_record['titles']
            # ['Sample Title : A Study / John Doe']
        """
        self.language = language

        result = super().do(blob, ignore_missing=ignore_missing, exception_handlers=exception_handlers)

        # Post-process title: extract bf:Title entries and format with subtitle
        # and responsibility statement for DC title element
        titles = blob.get("title", [])
        bf_titles = list(filter(lambda t: t.get("type") == "bf:Title", titles))

        if text := TitleExtension.format_text(
            titles=bf_titles,
            responsabilities=blob.get("responsibilityStatement", []),
            with_subtitle=True,
        ):
            result["titles"] = [text]

        # Prepend local PID as first identifier in bf:Local format
        if pid := blob.get("pid"):
            result.setdefault("identifiers", []).insert(0, f"bf:Local|{pid}")
        return result


dublincore = DublinCoreOverdo()


@dublincore.over("creators", "contribution")
@utils.for_each_value
@utils.ignore_value
def json_to_contributors(self, key, value):
    """Extract creators and contributors from contribution entities.

    This function implements role-based separation of creators vs contributors
    in Dublin Core. Contributors with roles in CREATOR_ROLES become dc:creator,
    while others become dc:contributor.

    :param self: The Dublin Core record being built.
    :type self: dict
    :param key: Source field key ("contribution").
    :type key: str
    :param value: Contribution object containing entity (with authorized_access_point)
        and role (list of MARC relator codes).
    :type value: dict
    :returns: Authorized access point if role is in CREATOR_ROLES, None otherwise
        (contributor added directly to self).
    :rtype: str or None

    Example::

        value = {
            'entity': {'authorized_access_point': 'Doe, John'},
            'role': ['aut']  # Author role
        }
        json_to_contributors(dc_record, 'contribution', value)
        # Returns: 'Doe, John'  # Added to dc:creator

        value['role'] = ['edt']  # Editor role
        json_to_contributors(dc_record, 'contribution', value)
        # Returns: None  # Added to dc:contributor instead
    """
    authorized_access_point = get_entity_localized_value(
        entity=value.get("entity", {}),
        key="authorized_access_point",
        language=dublincore.language,
    )
    result = authorized_access_point
    if result is None:
        result = value.get("entity", {}).get("authorized_access_point")

    if result:
        roles = value.get("role") or []
        if isinstance(roles, str):
            roles = [roles]
        if any(role in CREATOR_ROLES for role in roles):
            return result

        contributors = self.get("contributors", [])
        contributors.append(result)
        # save contributors directly into self
        self["contributors"] = contributors
    return None


@dublincore.over("descriptions", "^(summary|note|dissertation|supplementaryContent)")
@utils.ignore_value
def json_to_descriptions(self, key, value):
    """Aggregate description data from multiple RERO ILS fields into dc:description.

    Consolidates various descriptive fields into a single Dublin Core description
    element. This includes summaries, notes, dissertation information, and
    supplementary content.

    Field mappings:

    - supplementaryContent: Added directly
    - summary: Extracts all label values (multiple languages)
    - note: Extracts label field
    - dissertation: Extracts label field

    :param self: The Dublin Core record being built.
    :type self: dict
    :param key: Source field key (summary, note, dissertation, supplementaryContent).
    :type key: str
    :param value: Field value(s) to process. Can be string (supplementaryContent),
        dict with label (note or dissertation), or dict with label list (summary).
    :type value: list or dict
    :returns: None. Descriptions are written directly to self["descriptions"].
    :rtype: None

    .. note::

        - Accumulates values from multiple calls (all description sources)
        - Summary labels are flattened (all language variants included)
        - Empty descriptions list is not written to self

    Example::

        # First call with summary
        value = {'label': [{'value': 'A comprehensive study'}]}
        json_to_descriptions(dc, 'summary', value)
        dc['descriptions']
        # => ['A comprehensive study']

        # Second call with note
        value = {'label': 'Bibliography: p. 200-210'}
        json_to_descriptions(dc, 'note', value)
        dc['descriptions']
        # => ['A comprehensive study', 'Bibliography: p. 200-210']
    """
    descriptions = self.get("descriptions", [])
    for data in utils.force_list(value):
        if key == "supplementaryContent":
            descriptions.append(data)
        elif key == "summary":
            descriptions += [v for v in (label.get("value") for label in data.get("label", [])) if v is not None]
        elif label := data.get("label"):
            descriptions.append(label)
    if descriptions:
        # write the descriptions directly into self
        self["descriptions"] = descriptions


@dublincore.over("languages", "^language")
@utils.ignore_value
def json_to_languages(self, key, value):
    """Extract language codes for dc:language element.

    Converts RERO ILS language objects to simple ISO 639 language codes
    for Dublin Core.

    :param self: The Dublin Core record being built.
    :type self: dict
    :param key: Source field key ("language").
    :type key: str
    :param value: Language object(s) with value (ISO 639-2/B code) and
        optional type field.
    :type value: list or dict
    :returns: List of ISO 639 language codes, or None if no languages found.
    :rtype: list or None

    Example::

        value = [{'value': 'eng'}, {'value': 'fre'}]
        json_to_languages(dc, 'language', value)
        # Returns: ['eng', 'fre']
    """
    languages = [lang_code for language in utils.force_list(value) if (lang_code := language.get("value"))]
    return languages or None


@dublincore.over("publishers", "^provisionActivity")
@utils.ignore_value
def json_to_dates(self, key, value):
    """Extract publisher names and publication dates from provisionActivity.

    Processes provisionActivity to populate both dc:publisher and dc:date elements.
    Publisher names (dc:publisher) are extracted from all provisionActivity types,
    while publication dates (dc:date) are only extracted for bf:Publication activities.

    Extraction rules:

    - Date (dc:date): Only from bf:Publication, uses startDate and optional
      endDate, format "YYYY" or "YYYY-YYYY", only first publication date used
    - Publisher (dc:publisher): From bf:Agent statements, takes first label
      value, all agents included

    :param self: The Dublin Core record being built.
    :type self: dict
    :param key: Source field key ("provisionActivity").
    :type key: str
    :param value: List of provision activity objects with type, startDate,
        endDate, and statement fields.
    :type value: list
    :returns: None. Publishers and dates written directly to self["publishers"]
        and self["dates"].
    :rtype: None

    Example::

        value = [{
            'type': 'bf:Publication',
            'startDate': '2020',
            'endDate': '2023',
            'statement': [
                {
                    'type': 'bf:Agent',
                    'label': [{'value': 'Publisher Inc.'}]
                },
                {
                    'type': 'bf:Place',
                    'label': [{'value': 'New York'}]
                }
            ]
        }]
        json_to_dates(dc, 'provisionActivity', value)
        dc['dates']
        # => ['2020-2023']
        dc['publishers']
        # => ['Publisher Inc.']
    """
    publishers = self.get("publishers", [])
    dates = self.get("dates", [])
    for data in value:
        # Extract publication date (only from bf:Publication, and only once)
        # If we have startDate and endDate dates = f"{startDate}-{endDate}"
        # If we have no endDate but a startDate dates = f"{startDate}"
        # If we have no startDate but an endDate dates = f"-{endDate}"
        # If we have no startDate and no endDate, we don't add a date
        if data.get("type") == "bf:Publication" and not dates:
            start_date = str(data.get("startDate") or "")
            date = [start_date]
            if end_date := str(data.get("endDate") or ""):
                date.append(end_date)
            if start_date or end_date:
                dates.append("-".join(date))

        # Extract publisher names from bf:Agent type statements
        statements = data.get("statement", [])
        for statement in statements:
            if statement.get("type") == "bf:Agent":
                # Take first label value (publisher name) from agent statement
                labels = statement.get("label", [])
                if labels and (pub_name := labels[0].get("value")):
                    publishers.append(pub_name)
    # Write accumulated values to DC record
    if dates:
        self["dates"] = dates
    if publishers:
        self["publishers"] = publishers


@dublincore.over("types", "^type")
@utils.for_each_value
@utils.ignore_value
def json_to_types(self, key, value):
    """Convert document types to translated dc:type values.

    Transforms RERO ILS document type information into human-readable,
    translated type strings for Dublin Core. Combines main_type and
    optional subtype with translation.

    :param self: The Dublin Core record being built.
    :type self: dict
    :param key: Source field key ("type").
    :type key: str
    :param value: Type object containing main_type and optional subtype codes.
    :type value: dict
    :returns: Translated type string. Format "Main Type / Subtype" with subtype
        or "Main Type" without.
    :rtype: str

    Example::

        value = {'main_type': 'docmaintype_book', 'subtype': 'docsubtype_e-book'}
        json_to_types(dc, 'type', value)  # Language: en
        # Returns: 'Book / E-book'

        value = {'main_type': 'docmaintype_serial'}
        json_to_types(dc, 'type', value)  # Language: fr
        # Returns: 'Périodique'
    """
    main_type = value.get("main_type")
    if subtype_type := value.get("subtype"):
        return " / ".join([_(main_type), _(subtype_type)])
    return _(main_type)


@dublincore.over("identifiers", "^identifiedBy")
@utils.for_each_value
@utils.ignore_value
def json_to_identifiers(self, key, value):
    """Convert various identifier types to dc:identifier format.

    Transforms RERO ILS identifier objects into formatted strings for Dublin Core.
    Supports multiple identifier types (ISBN, ISSN, DOI, etc.) with optional
    source information.

    Output format:

    - With source: "Type|(Source)Value" (e.g., "bf:Doi|(CrossRef)10.1000/xyz")
    - Without source: "Type|Value" (e.g., "bf:Isbn|9781234567890")

    :param self: The Dublin Core record being built.
    :type self: dict
    :param key: Source field key ("identifiedBy").
    :type key: str
    :param value: Identifier object containing type, value, optional source,
        and optional status.
    :type value: dict
    :returns: Formatted identifier string.
    :rtype: str

    .. note::

        - Type prefix uses BIBFRAME vocabulary (bf:Isbn, bf:Issn, etc.)
        - Source is included in parentheses when present
        - Invalid/cancelled identifiers are still included
        - Local PID is prepended separately in do() method

    Example::

        value = {'type': 'bf:Isbn', 'value': '9781234567890'}
        json_to_identifiers(dc, 'identifiedBy', value)
        # Returns: 'bf:Isbn|9781234567890'

        value = {
            'type': 'bf:Doi',
            'value': '10.1000/xyz',
            'source': 'CrossRef'
        }
        json_to_identifiers(dc, 'identifiedBy', value)
        # Returns: 'bf:Doi|(CrossRef)10.1000/xyz'
    """
    itype = value.get("type")
    identifier_value = value.get("value")
    if not itype or not identifier_value:
        return None
    if source := value.get("source"):
        return f"{itype}|({source}){identifier_value}"
    return f"{itype}|{identifier_value}"


@dublincore.over(
    "relations",
    "^(issuedWith|otherEdition|otherPhysicalFormat|precededBy|relatedTo|succeededBy|supplement|supplementTo)",
)
@utils.for_each_value
@utils.ignore_value
def json_to_relations(self, key, value):
    """Extract related work information for dc:relation element.

    Consolidates various relationship fields into dc:relation. Supports both
    labeled relationships (with explicit label) and title-based relationships
    (with title array).

    :param self: The Dublin Core record being built.
    :type self: dict
    :param key: Source field key (relationship type).
    :type key: str
    :param value: Relationship object containing label or title array with
        _text field.
    :type value: dict
    :returns: Relationship description string, or None if neither label nor
        titles are present.
    :rtype: str or None

    .. note::

        - Prefers label over title if both present
        - Multiple titles are joined with ", "
        - Relationship type is not included in output (lost in consolidation)

    Example::

        value = {'label': 'Earlier edition: 1st ed., 2010'}
        json_to_relations(dc, 'precededBy', value)
        # Returns: 'Earlier edition: 1st ed., 2010'

        value = {'title': [{'_text': 'Original French'}, {'_text': 'German trans.'}]}
        json_to_relations(dc, 'otherEdition', value)
        # Returns: 'Original French, German trans.'
    """
    if label := value.get("label"):
        return label
    if titles := [t for title in value.get("title", []) if (t := title.get("_text"))]:
        return ", ".join(titles)
    return None


@dublincore.over("subjects", "^subjects")
@utils.for_each_value
@utils.ignore_value
def json_to_subject(self, key, value):
    """Convert subject entities to dc:subject strings.

    Transforms various entity types into subject heading strings for Dublin Core.
    Handles different entity types with type-specific formatting and language-aware
    resolution for authorized access points.

    :param self: The Dublin Core record being built.
    :type self: dict
    :param key: Source field key ("subjects").
    :type key: str
    :param value: Subject entity object containing type, authorized_access_point,
        preferred_name, creator, title, or term depending on entity type.
    :type value: dict
    :returns: Subject heading string, or None if no suitable value found.
    :rtype: str or None

    .. note::

        - Uses get_entity_localized_value() for language-aware resolution
        - WORK subjects include creator if available
        - Empty results return None instead of empty string

    Example::

        # Person subject
        value = {
            'type': 'bf:Person',
            'authorized_access_point': 'Shakespeare, William, 1564-1616'
        }
        json_to_subject(dc, 'subjects', value)
        # Returns: 'Shakespeare, William, 1564-1616'

        # Work subject
        value = {
            'type': 'bf:Work',
            'creator': 'Homer',
            'title': 'Odyssey'
        }
        json_to_subject(dc, 'subjects', value)
        # Returns: 'Homer. - Odyssey'

        # Topic subject
        value = {'type': 'bf:Topic', 'term': 'Artificial intelligence'}
        json_to_subject(dc, 'subjects', value)
        # Returns: 'Artificial intelligence'
    """
    result = ""
    _type = value.get("type")

    # Person, organisation, or place subjects: use authorized access point
    if _type in [EntityType.PERSON, EntityType.ORGANISATION, EntityType.PLACE]:
        if authorized_access_point := get_entity_localized_value(
            entity=value,
            key="authorized_access_point",
            language=dublincore.language,
        ):
            result = authorized_access_point
        else:
            result = value.get("preferred_name")

    # Work subjects: combine creator and title
    elif _type == EntityType.WORK:
        work = []
        if creator := value.get("creator"):
            work.append(creator)
        if title := value.get("title"):
            work.append(title)
        result = ". - ".join(work)

    # Topic or temporal subjects: use term
    elif _type in [EntityType.TOPIC, EntityType.TEMPORAL]:
        result = value.get("term")

    return result or None
