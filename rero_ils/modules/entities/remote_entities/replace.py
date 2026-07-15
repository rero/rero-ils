# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Replace identifiedBy with $ref from MEF."""

import contextlib
from copy import deepcopy
from datetime import UTC, datetime

import requests
from flask import current_app
from sqlalchemy.orm.exc import NoResultFound

from rero_ils.modules.documents.api import Document, DocumentsSearch
from rero_ils.modules.utils import get_mef_url, get_timestamp, requests_retry_session
from rero_ils.modules.utils import set_timestamp as utils_set_timestamp

from ..logger import create_logger
from .api import RemoteEntity

# (connect, read) timeout in seconds for each MEF request, so a stalled
# connection cannot hang the whole run scan.
MEF_REQUEST_TIMEOUT = (5, 60)


class ReplaceIdentifiedBy:
    """Replace a document's ``identifiedBy`` entities with a MEF ``$ref``.

    For a given field (``contribution``, ``subjects`` or ``genreForm``), every
    entity still described by a local ``identifiedBy`` is looked up on the MEF
    server; when a match is found the entity is rewritten as a ``$ref`` to the
    MEF record. The identifier alone is authoritative — a wrong local type does
    not prevent linking.

    Outcomes are accumulated in per-entity-type dicts for reporting:

    * ``not_found``: the identifier was not found on any allowed MEF family.
    * ``rero_only``: found, but the MEF record exposes only a RERO source
      (nothing to link to); also gates retries for the same identifier.
    * ``type_mismatch``: (``contribution`` only) linked, but the MEF type
      differs from the document's — still a valid contribution type, flagged
      for review.
    * ``type_not_allowed``: the MEF type cannot appear in this field at all
      (e.g. a contribution resolving to a ``bf:Topic``) — refused, not linked,
      logged as an error.

    Usage example::

        replace = ReplaceIdentifiedBy(field="contribution", dry_run=True, verbose=True)
        changed, not_found, rero_only = replace.run()
    """

    fields = ("contribution", "subjects", "genreForm")
    # MEF families allowed for each field, per the document JSON schema.
    field_mef_types = {
        "contribution": ("agents",),
        "subjects": ("agents", "concepts", "places"),
        "genreForm": ("concepts",),
    }
    timestamp_name = "replace_identified_by"

    def __init__(self, field, dry_run=False, verbose=False, log_dir=None):
        """Initialize the replacer for a single document field.

        :param field: the field to process: contribution, subjects or genreForm.
        :param dry_run: when True, resolve and report but do not write changes.
        :param verbose: verbosity level (bool or integer).
        :param log_dir: directory for the ``replace_identifiedby.log`` file;
            when omitted, logs go to the default location.
        """
        self.field = field
        self.dry_run = dry_run
        self.verbose = verbose
        self.entity_types = current_app.config["RERO_ILS_ENTITY_TYPES"]
        # Entity types allowed in this field, per RERO_ILS_ENTITIES_TYPES_FIELDS.
        types_fields = current_app.config["RERO_ILS_ENTITIES_TYPES_FIELDS"]
        self.allowed_entity_types = {entity_type for entity_type, fields in types_fields.items() if field in fields}
        self.logger = create_logger(
            name="ReplaceIdentifiedBy",
            file_name="replace_identifiedby.log",
            log_dir=log_dir,
            verbose=verbose,
        )
        self.changed = 0
        self.rero_only = {}
        self.not_found = {}
        self.type_mismatch = {}
        self.type_not_allowed = {}

    def _get_base_url(self, entity_type):
        """Return the MEF base URL for a MEF family.

        :param entity_type: MEF family (agents, concepts, places).
        :returns: the base URL for that family.
        :raises KeyError: when no base URL is configured for the family.
        """
        if base_url := get_mef_url(entity_type):
            return base_url
        raise KeyError(f"Unable to find MEF base url for {entity_type}")

    def _get_latest(self, entity_type, source, pid):
        """Fetch the latest MEF record for a source identifier.

        :param entity_type: MEF family (agents, concepts, places).
        :param source: the identifier source, such as `idref` or `gnd`.
        :param pid: the identifier value in that source.
        :returns: the MEF record, or an empty dict on any non-OK response.
        """
        url = f"{self._get_base_url(entity_type)}/mef/latest/{source}:{pid}"
        res = requests_retry_session().get(url, timeout=MEF_REQUEST_TIMEOUT)
        if res.status_code == requests.codes.ok:
            return res.json()
        self.logger.warning("Problem get %s: %s", url, res.status_code)
        return {}

    def _get_latest_for_field(self, doc_entity_type, source, pid):
        """Query the MEF families allowed for the current field.

        The MEF family implied by the document's local type is tried first,
        then the field's other allowed families, so a wrong local type does
        not prevent finding the identifier: it alone is enough to link.

        :param doc_entity_type: (string) the entity type declared in the document.
        :param source: (string) the entity source such as `idref`, `gnd`.
        :param pid: (string) the entity identifier.
        :returns: (mef_type, mef_data) the family the record was found in and
            the MEF record, or (None, {}) if not found in any allowed family.
        """
        guessed_mef_type = self.entity_types.get(doc_entity_type)
        if guessed_mef_type is None:
            # `doc_entity_type` has no MEF family at all (e.g. bf:Work): nothing to query.
            return None, {}
        allowed_mef_types = self.field_mef_types[self.field]
        for mef_type in dict.fromkeys((guessed_mef_type, *allowed_mef_types)):
            if mef_type in allowed_mef_types and (mef_data := self._get_latest(mef_type, source, pid)):
                return mef_type, mef_data
        return None, {}

    def _find_other_source(self, source, mef_data):
        """Pick the source to link to from a MEF record.

        `idref`/`gnd` are linkable and returned as-is; a `rero` source is not
        linkable, so the record is searched for an `idref` or `gnd` alternative.

        :param source: the document's identifier source (idref, gnd or rero).
        :param mef_data: the MEF record to inspect.
        :returns: a (source, pid) tuple to link to, or (None, None) when the
            record exposes no linkable source.
        """
        if source in ("idref", "gnd"):
            return source, mef_data[source]["pid"]
        if source == "rero":
            for new_source in ("idref", "gnd"):
                if source_data := mef_data.get(new_source):
                    return new_source, source_data["pid"]
        return None, None

    @property
    def query(self):
        """Search query for documents with identifiedBy and entity types."""
        return (
            DocumentsSearch()
            .filter("exists", field=f"{self.field}.entity.identifiedBy")
            .filter({"terms": {f"{self.field}.entity.type": list(self.allowed_entity_types)}})
        )

    def count(self):
        """Get count of Documents with identifiedBy."""
        return self.query.count()

    def _create_entity(self, mef_type, mef_data):
        """Create entity if not exists.

        :param mef_type: MEF type (agent, concept)
        :param mef_data: MEF data for entity.
        """
        if not RemoteEntity.get_record_by_pid(mef_data["pid"]):
            if not self.dry_run:
                new_mef_data = deepcopy(mef_data)
                fields_to_remove = ["$schema", "_created", "_updated"]
                for field in fields_to_remove:
                    new_mef_data.pop(field, None)
                # TODO: try to optimize with parent commit and reindex
                #       bulk operation
                RemoteEntity.create(data=new_mef_data, dbcommit=True, reindex=True)
            self.logger.info("Create a new MEF %s record(pid: %s)", mef_type, mef_data["pid"])

    def _do_entity(self, entity, doc_pid):
        """Resolve one entity and rewrite it as a MEF ``$ref`` when possible.

        Looks the entity's identifier up on the allowed MEF families and, on a
        linkable match, replaces ``entity["entity"]`` in place with a ``$ref``.
        Unresolved, RERO-only, type-mismatch and type-not-allowed outcomes are
        recorded in the corresponding reporting dicts (see the class docstring).

        :param entity: the field entry to process; mutated in place on success.
        :param doc_pid: the document pid, used for logging.
        :returns: True if the entity was linked, False/None otherwise (None when
            skipped without a change, e.g. already-tried or type-not-allowed).
        """
        changed = False
        doc_entity_type = entity["entity"]["type"]
        source_pid = entity["entity"]["identifiedBy"]["value"]
        source = entity["entity"]["identifiedBy"]["type"].lower()
        identifier = f"{source}:{source_pid}"
        if (
            identifier in self.not_found.get(doc_entity_type, {})
            or identifier in self.rero_only.get(doc_entity_type, {})
            or identifier in self.type_not_allowed.get(doc_entity_type, {})
        ):
            # Already resolved to a deterministic no-link outcome; don't query
            # MEF again. (type_mismatch is excluded: those entities DO link, so
            # a later document sharing the identifier must still be replaced.)
            return None
        mef_type, mef_data = self._get_latest_for_field(doc_entity_type, source, source_pid)
        if mef_data:
            new_source, new_source_pid = self._find_other_source(source=source, mef_data=mef_data)
            if new_source:
                mef_entity_type = mef_data.get("type")
                source_authorized_access_point = mef_data.get(source, {}).get("authorized_access_point")
                if mef_entity_type and mef_entity_type not in self.allowed_entity_types:
                    # The identifier resolves to an entity whose type cannot appear
                    # in this field (e.g. a contribution pointing to a bf:Topic):
                    # do not link it — a wrong-typed $ref would be invalid data.
                    info = (
                        f"{doc_entity_type} -> {mef_entity_type} not allowed "
                        f'for {self.field} : "{source_authorized_access_point}"'
                    )
                    self.type_not_allowed.setdefault(doc_entity_type, {})[identifier] = info
                    self.logger.error(
                        "Type not allowed:%s %s - (%s) %s %s", doc_pid, self.field, mef_type, identifier, info
                    )
                    return None
                self._create_entity(mef_type, mef_data)
                authorized_access_point = entity["entity"]["authorized_access_point"]
                mef_authorized_access_point = mef_data[new_source]["authorized_access_point"]
                self.logger.info(
                    'Replace document:%s %s "%s" - (%s:%s) %s:%s "%s"',
                    doc_pid,
                    self.field,
                    authorized_access_point,
                    mef_type,
                    mef_data["pid"],
                    new_source,
                    new_source_pid,
                    mef_authorized_access_point,
                )
                entity["entity"] = {
                    "$ref": (f"{self._get_base_url(mef_type)}/{new_source}/{new_source_pid}"),
                    "pid": mef_data["pid"],
                }
                changed = True
                # the identifier alone is enough to link the entity; on
                # `contribution` a type mismatch (within the allowed types) is
                # still flagged for review. Kept separate from `rero_only`,
                # which also gates retries: this entity was successfully
                # replaced, so it must not block a later document sharing the
                # same identifier.
                if self.field == "contribution" and mef_entity_type != doc_entity_type:
                    info = f'{doc_entity_type} != {mef_entity_type} : "{source_authorized_access_point}"'
                    self.type_mismatch.setdefault(doc_entity_type, {})[identifier] = info
                    self.logger.warning(
                        "Type differ:%s %s - (%s) %s %s", doc_pid, self.field, mef_type, identifier, info
                    )
            else:
                authorized_access_point = mef_data.get(source, {}).get("authorized_access_point")
                info = f"{authorized_access_point}"
                self.rero_only.setdefault(doc_entity_type, {})[identifier] = info
                self.logger.info(
                    'No other source found for document:%s %s - (%s|%s) %s "%s"',
                    doc_pid,
                    self.field,
                    mef_type,
                    doc_entity_type,
                    identifier,
                    info,
                )
        else:
            authorized_access_point = entity["entity"]["authorized_access_point"]
            info = f"{authorized_access_point}"
            self.not_found.setdefault(doc_entity_type, {})[identifier] = info
            self.logger.info(
                'No MEF found for document:%s  - (%s) %s "%s"',
                doc_pid,
                doc_entity_type,
                identifier,
                info,
            )
        return changed

    def _replace_entities_in_document(self, doc_id):
        """Replace every resolvable ``identifiedBy`` entity in one document.

        A failure on a single entity is logged and skipped so it never aborts
        the rest of the document.

        :param doc_id: the document record id (uuid).
        :returns: the mutated document when at least one entity changed, else
            None (nothing to persist).
        """
        changed = False
        with contextlib.suppress(NoResultFound):
            doc = Document.get_record(doc_id)
            entities_to_update = filter(
                lambda c: c.get("entity", {}).get("identifiedBy"),
                doc.get(self.field, {}),
            )
            for entity in entities_to_update:
                try:
                    changed = self._do_entity(entity, doc.pid) or changed
                except Exception as err:
                    self.logger.error("Error document:%s %s %s", doc.pid, entity, err)
            if changed:
                return doc
        return None

    def _error_count(self, counter_dict):
        """Sum the entries across a per-entity-type reporting dict.

        :param counter_dict: a ``{entity_type: {identifier: info}}`` dict.
        :returns: the total number of identifiers recorded in it.
        """
        return sum(len(values) for values in counter_dict.values())

    def run(self):
        """Process the whole field: resolve and persist every document.

        Scans documents that still carry an ``identifiedBy`` for the field,
        rewrites resolvable entities as ``$ref`` (unless dry-run), and records
        the run in the timestamp store.

        ``type_mismatch`` and ``type_not_allowed`` counts are not in this tuple;
        they are exposed via the same-named attributes and the timestamp payload.

        :returns: a (changed, not_found, rero_only) tuple of counts.
        """
        self.changed = 0
        self.not_found = {}
        self.rero_only = {}
        self.type_mismatch = {}
        self.type_not_allowed = {}
        self.logger.info("Found %s identifiedBy: %s", self.field, self.count())
        query = self.query.params(preserve_order=True).sort({"_created": {"order": "asc"}}).source(["pid", self.field])
        for hit in list(query.scan()):
            if doc := self._replace_entities_in_document(hit.meta.id):
                self.changed += 1
                if not self.dry_run:
                    doc.update(data=doc, dbcommit=True, reindex=True)
        self.set_timestamp()
        return (
            self.changed,
            self._error_count(self.not_found),
            self._error_count(self.rero_only),
        )

    def get_timestamp(self):
        """Get time stamp."""
        if data := get_timestamp("replace_identified_by"):
            data.pop("name", None)
        return data or {}

    def set_timestamp(self):
        """Record per-field outcome counts in the timestamp store.

        Each outcome is reported under its own key so none is absorbed into
        another:
        * not found: the identifier was not found on any allowed MEF family.
        * rero only: found, but the MEF record exposes only a `rero` source.
        * type mismatch: linked, but the MEF type differs (contribution only).
        * type not allowed: the MEF type cannot appear in this field (refused).
        """
        data = self.get_timestamp()
        data[self.field] = {
            "changed": self.changed,
            "not found": self._error_count(self.not_found),
            "rero only": self._error_count(self.rero_only),
            "type mismatch": self._error_count(self.type_mismatch),
            "type not allowed": self._error_count(self.type_not_allowed),
            "time": datetime.now(UTC),
        }
        utils_set_timestamp(self.timestamp_name, **data)
