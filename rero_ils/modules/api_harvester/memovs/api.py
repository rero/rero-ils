# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""API for Memovs audiovisual archives records."""

import traceback

from deepdiff import DeepDiff
from flask import current_app
from requests import codes as requests_codes

from rero_ils.modules.api import IlsRecordsIndexer
from rero_ils.modules.documents.api import Document, DocumentsSearch
from rero_ils.modules.holdings.api import Holding
from rero_ils.modules.items.api import Item, ItemsSearch
from rero_ils.modules.local_fields.api import LocalField, LocalFieldsSearch
from rero_ils.modules.locations.api import Location
from rero_ils.modules.utils import (
    JsonWriter,
    extracted_data_from_ref,
    get_ref_for_pid,
    get_schema_for_resource,
    requests_retry_session,
)

from ..api import ApiHarvest
from ..models import HarvestActionType
from .dojson.json import memovs_json


class ApiMemovs(ApiHarvest):
    """ApiMemovs class.

    Class for harvesting audiovisual archives from Memovs API.
    """

    def __init__(self, name, file_name=None, process=False, harvest_count=-1, verbose=False, log_file=None):
        """Class init."""
        super().__init__(
            name=name,
            process=process,
            harvest_count=harvest_count,
            verbose=verbose,
            log_file=log_file,
        )
        if file_name:
            self.file = JsonWriter(file_name)
        # Reused across page fetches (HTTP keep-alive); lazily created, see `session`.
        self._session = None
        self._vendor = "MEMOVS"
        self._last_doc_pid = None
        # Populated by _build_caches() before the harvest loop.
        self._existing_docs = {}  # harvested_id -> doc_pid
        self._items_cache = {}  # doc_pid -> {call_number -> item_pid}
        self._lofis_cache = None  # doc_pid -> lofi_pid; None = cache not built
        self._cached_org_pid = None  # organisation_pid derived from location_pid

    @property
    def session(self):
        """Retry session reused for page fetches (HTTP keep-alive).

        Lazily created so it also works when the instance is built without
        __init__ (e.g. in tests); shared with the transformer so MEF lookups
        reuse the same connections.
        """
        if getattr(self, "_session", None) is None:
            self._session = requests_retry_session()
            memovs_json.session = self._session
        return self._session

    def msg_text(self, pid, msg):
        """Logging message text with document pid.

        :param pid: harvested pid for message text
        :param msg: msg text for message
        :returns: string message
        """
        base = super().msg_text(pid=pid, msg=msg)
        return f"{base} doc:{self._last_doc_pid}" if self._last_doc_pid else base

    def get_request_url(self, start_date="1990-01-01", page=1):
        """Get request URL.

        :param start_date: date from where records has to be harvested
        :param page: page from where records have to be harvested
        :returns: request url
        """
        params = f"from={start_date}&currentPage={page}"
        return f"{self._url}?{params}"

    def _build_caches(self):
        """Pre-build in-memory caches to eliminate per-record ES queries.

        Builds three dicts from single ES scans:

        * ``_existing_docs``: ``harvested_id -> doc_pid`` — replaces the
          per-record ``DocumentsSearch`` existence check in
          ``create_update_record``.
        * ``_items_cache``: ``doc_pid -> {call_number -> item_pid}`` —
          replaces the per-document ``ItemsSearch`` in ``sync_items`` and
          ``delete_items``.
        * ``_lofis_cache``: ``doc_pid -> lofi_pid`` — replaces the
          per-record ``LocalFieldsSearch`` existence check in
          ``sync_local_field``; also caches the derived ``_cached_org_pid``.
        """
        self.verbose_print(f"{self._vendor}: building document existence cache…")
        self._existing_docs = {}
        for hit in (
            DocumentsSearch().filter("term", identifiedBy__source=self._vendor).source(["pid", "identifiedBy"]).scan()
        ):
            for ident in hit.to_dict().get("identifiedBy") or []:
                if ident.get("source") == self._vendor:
                    self._existing_docs[ident["value"]] = hit.pid

        settings = self.config.settings or {}
        location_pid = settings.get("location_pid")
        item_type_pid = settings.get("item_type_pid")

        self._cached_org_pid = None
        if location_pid:
            if location := Location.get_record_by_pid(location_pid):
                self._cached_org_pid = location.organisation_pid

        self._items_cache = {}
        if location_pid and item_type_pid:
            self.verbose_print(f"{self._vendor}: building items cache for location {location_pid}…")
            for hit in (
                ItemsSearch()
                .filter("term", location__pid=location_pid)
                .filter("term", item_type__pid=item_type_pid)
                .source(["pid", "document", "call_number"])
                .scan()
            ):
                if doc_pid := hit.to_dict().get("document", {}).get("pid"):
                    call_number = getattr(hit, "call_number", "") or ""
                    self._items_cache.setdefault(doc_pid, {})[call_number] = hit.pid

        self._lofis_cache = {}
        if self._cached_org_pid:
            self.verbose_print(f"{self._vendor}: building local fields cache for org {self._cached_org_pid}…")
            for hit in (
                LocalFieldsSearch()
                .filter("term", organisation__pid=self._cached_org_pid)
                .filter("term", parent__type="doc")
                .source(["pid", "parent"])
                .scan()
            ):
                if parent_pid := hit.to_dict().get("parent", {}).get("pid"):
                    self._lofis_cache[parent_pid] = hit.pid

    @staticmethod
    def _delete_items(pids):
        """Delete items by PID, silently skipping any that no longer exist.

        :param pids: iterable of item PIDs.
        """
        for pid in pids:
            if item := Item.get_record_by_pid(pid):
                item.delete(dbcommit=True, delindex=True)

    def delete_items(self, document_pid):
        """Delete all harvested items for a document.

        Uses ``_items_cache`` when available; falls back to an ES query.

        :param document_pid: document pid
        """
        settings = self.config.settings or {}
        location_pid = settings.get("location_pid")
        item_type_pid = settings.get("item_type_pid")
        if not (location_pid and item_type_pid):
            return

        cached = self._items_cache.pop(document_pid, None)
        if cached is not None:
            self._delete_items(cached.values())
            return

        # Fallback: cache not yet populated or document not in cache.
        query = (
            ItemsSearch()
            .filter("term", document__pid=document_pid)
            .filter("term", location__pid=location_pid)
            .filter("term", item_type__pid=item_type_pid)
            .source(["pid"])
        )
        self._delete_items(hit.pid for hit in query.scan())

    #: bf:note types that are stored as local fields (everything else, e.g.
    #: the "general" type, becomes a document note in the dojson transformation).
    LOCAL_FIELD_NOTE_TYPES = ("vsavmat", "vsavgeo", "vsavfonds")

    @staticmethod
    def _extract_local_fields(data):
        """Extract bf:note label strings destined for a LocalField record.

        Only notes whose ``bf:noteType`` is one of
        :data:`LOCAL_FIELD_NOTE_TYPES` are kept.

        :param data: raw Memovs record dict.
        :returns: list of label strings.
        """
        local_fields = []
        for item in data.get("bf:note", []):
            label = item.get("rdfs:label", "")
            if label and item.get("bf:noteType", "").lower() in ApiMemovs.LOCAL_FIELD_NOTE_TYPES:
                local_fields.append(label)
        return local_fields

    @staticmethod
    def _document_differs(doc, record_data):
        """Whether the harvested data differs from the stored document.

        Entity ``pid`` values (subjects/contribution/genreForm) are injected
        into the stored document by ``AddMEFPidExtension`` and are absent from
        the freshly transformed data, so every ``pid`` path is ignored — the
        source-driven ``$ref`` is still compared, so a real change is never
        masked. This is the only store-time mutation for Memovs documents.

        :param doc: the existing Document record.
        :param record_data: the freshly transformed record data (pid already set).
        :returns: True when the content differs.
        """
        ignore = {"_created", "_updated"}
        old = {k: v for k, v in doc.items() if k not in ignore}
        new = {k: v for k, v in record_data.items() if k not in ignore}
        return bool(DeepDiff(old, new, exclude_regex_paths=[r"\['pid'\]"]))

    def sync_local_field(self, document_pid, local_fields):
        """Create or update the local field record that holds bf:note labels for a document.

        The organisation is derived from ``location_pid`` in the harvester settings.
        The target field name is read from ``local_field_name`` (defaults to ``field_2``).
        When ``local_fields`` is empty the existing local field is deleted.

        When ``_lofis_cache`` is populated (batch harvest mode) the ES existence
        query is replaced by a dict lookup and writes are deferred to the next
        ``_flush_pending`` call.

        :param document_pid: the RERO-ILS document PID.
        :param local_fields: list of label strings extracted from bf:note.
        :returns: True when the local field was created, updated or deleted.
        """
        settings = self.config.settings or {}
        field_name = settings.get("local_field_name", "field_2")

        lofis_cache = getattr(self, "_lofis_cache", None)
        if lofis_cache is not None:
            organisation_pid = getattr(self, "_cached_org_pid", None)
            lofi_pid = lofis_cache.get(document_pid)
            existing = LocalField.get_record_by_pid(lofi_pid) if lofi_pid else None
        else:
            organisation_pid = None
            if location_pid := settings.get("location_pid"):
                if location := Location.get_record_by_pid(location_pid):
                    organisation_pid = location.organisation_pid
                else:
                    current_app.logger.warning(
                        f"sync_local_field: location {location_pid!r} not found, skipping doc:{document_pid}"
                    )
                    return False
            existing = next(LocalField.get_local_fields_by_id("doc", document_pid, organisation_pid), None)

        if not local_fields:
            if existing:
                if lofis_cache is not None:
                    lofis_cache.pop(document_pid, None)
                existing.delete(dbcommit=True, delindex=True)
                return True
            return False

        lofi_data = {
            "$schema": get_schema_for_resource("lofi"),
            "parent": {"$ref": get_ref_for_pid("doc", document_pid)},
            "fields": {field_name: local_fields},
        }
        if organisation_pid:
            lofi_data["organisation"] = {"$ref": get_ref_for_pid("org", organisation_pid)}

        # Skip the rewrite when the stored fields already match.
        if existing and existing.get("fields") == lofi_data["fields"]:
            return False

        if existing:
            existing.replace(data={**lofi_data, "pid": existing.pid}, dbcommit=True, reindex=True)
        else:
            record = LocalField.create(data=lofi_data, dbcommit=True, reindex=True)
            if lofis_cache is not None:
                lofis_cache[document_pid] = record.pid
        return True

    @staticmethod
    def _extract_call_number(part):
        """Extract call number from a bf:hasPart element.

        :param part: bf:hasPart dict from source data
        :returns: call number string, or empty string if not found
        """
        for identifier in part.get("bf:identifier", []):
            if value := identifier.get("rdf:value"):
                return value
        return ""

    def sync_items(self, document_pid, has_parts, url=None):
        """Synchronise items with bf:hasPart data.

        Creates items for new call numbers, deletes items whose call number is
        no longer in has_parts, and leaves unchanged items untouched. When
        has_parts is empty but a URL is provided, a single item is created
        whose call_number is the last path segment of the URL.

        Uses ``_items_cache`` to avoid per-document ES queries; the cache is
        updated in place so subsequent calls for the same document are correct.

        :param document_pid: document pid
        :param has_parts: list of bf:hasPart elements from source data
        :param url: landing page URL, used to derive call_number when has_parts is empty
        :returns: True when any item was created or deleted.
        """
        settings = self.config.settings or {}
        location_pid = settings.get("location_pid")
        item_type_pid = settings.get("item_type_pid")
        if not (location_pid and item_type_pid):
            return False

        # Index new parts by call number; for URL-only records use the last URL path segment
        new_call_numbers = {self._extract_call_number(part): part for part in has_parts}
        if not has_parts and url:
            new_call_numbers[url.rstrip("/").split("/")[-1]] = None

        # Use cached items; fall back to ES query when cache is absent.
        if document_pid in self._items_cache:
            existing_items = self._items_cache[document_pid]
        else:
            existing_items = {}
            query = (
                ItemsSearch()
                .filter("term", document__pid=document_pid)
                .filter("term", location__pid=location_pid)
                .filter("term", item_type__pid=item_type_pid)
                .source(["pid", "call_number"])
            )
            for hit in query.scan():
                call_number = getattr(hit, "call_number", "") or ""
                existing_items[call_number] = hit.pid

        # Delete items whose call number is no longer present
        removed_call_numbers = set(existing_items) - set(new_call_numbers)
        for call_number in removed_call_numbers:
            if item := Item.get_record_by_pid(existing_items[call_number]):
                item.delete(dbcommit=True, delindex=True)

        new_items = {}
        indexed_holding_pids = set()
        for call_number in set(new_call_numbers) - set(existing_items):
            item_data = {
                "$schema": get_schema_for_resource("item"),
                "document": {"$ref": get_ref_for_pid("doc", document_pid)},
                "item_type": {"$ref": get_ref_for_pid("itty", item_type_pid)},
                "location": {"$ref": get_ref_for_pid("loc", location_pid)},
                "pac_code": "0_frozen_collection",
                "status": "on_shelf",
                "type": "standard",
                "call_number": call_number,
                "harvested": True,
            }
            item = Item.create(data=item_data, dbcommit=True, reindex=False)
            holding_pid = extracted_data_from_ref(item.get("holding"))
            # Index item and holding directly without cascade so the holding is findable in ES
            # by subsequent items. The cascade (holding → document + entity queries) only
            # happens once per holding in the final loop below.
            IlsRecordsIndexer().index(item)
            if holding_pid not in indexed_holding_pids:
                if holding := Holding.get_record_by_pid(holding_pid):
                    IlsRecordsIndexer().index(holding)
                indexed_holding_pids.add(holding_pid)
            new_items[call_number] = item

        for holding_pid in indexed_holding_pids:
            if holding := Holding.get_record_by_pid(holding_pid):
                holding.reindex()

        # Update cache: keep surviving call numbers, add newly created ones
        self._items_cache[document_pid] = {cn: pid for cn, pid in existing_items.items() if cn in new_call_numbers} | {
            cn: item.pid for cn, item in new_items.items()
        }

        return bool(removed_call_numbers or new_items)

    def create_update_record(self, record):
        """Create, update or delete record.

        :param record: data for record operation
        :returns: harvested id and status
        """
        record_id = record.get("@id", "")
        try:
            status = HarvestActionType.NOTSET
            doc_record = None
            record_data = memovs_json.do(record)
            if record_data.pop("deleted", None):
                status = HarvestActionType.DELETED
            has_parts = record.get("bf:hasPart", [])

            # Extract landing page URL from electronicLocator
            elocs = record.get("bf:electronicLocator", [])
            url = next(
                (e.get("@id") for e in elocs if e.get("bf:noteType") == "landingPage"),
                None,
            )

            # Get harvested ID; use cache to avoid a per-record ES round-trip.
            harvested_id = record_data.pop("pid")
            pid = self._existing_docs.get(harvested_id)

            local_fields = self._extract_local_fields(record)

            self._last_doc_pid = None
            if pid:
                if doc := Document.get_record_by_pid(pid):
                    if status == HarvestActionType.DELETED:
                        self._count_del += 1
                        self._last_doc_pid = doc.pid
                        self.delete_items(document_pid=doc.pid)
                        # Try to delete document (local fields are cascade-deleted via DeleteRelatedLocalFieldExtension)
                        doc.pop("harvested", None)
                        if not doc.reasons_not_to_delete():
                            doc.delete(dbcommit=True, delindex=True)
                            self._existing_docs.pop(harvested_id, None)
                    else:
                        record_data["pid"] = doc.pid
                        # Only replace (and reindex) the document when it changed;
                        # items and local fields are synced independently below.
                        if doc_changed := self._document_differs(doc, record_data):
                            doc = doc.replace(data=record_data, dbcommit=True, reindex=True)
                        self._last_doc_pid = doc.pid
                        items_changed = self.sync_items(document_pid=doc.pid, has_parts=has_parts, url=url)
                        lofi_changed = self.sync_local_field(document_pid=doc.pid, local_fields=local_fields)
                        if doc_changed or items_changed or lofi_changed:
                            self._count_upd += 1
                            status = HarvestActionType.UPDATED
                        else:
                            self._count_unchanged += 1
                            status = HarvestActionType.UNCHANGED
            elif status == HarvestActionType.NOTSET:
                self._count_new += 1
                status = HarvestActionType.CREATED
                doc_record = Document.create(data=record_data, dbcommit=True, reindex=True)
                self._existing_docs[harvested_id] = doc_record.pid
                self._last_doc_pid = doc_record.pid
                self.sync_items(document_pid=doc_record.pid, has_parts=has_parts, url=url)
                self.sync_local_field(document_pid=doc_record.pid, local_fields=local_fields)
            return harvested_id, status
        except Exception as err:
            # Never let one malformed record abort the whole harvest; log and skip it.
            # Point at the deepest frame so the failing step (e.g. a trans_* method
            # and line) is visible instead of just the exception message.
            frame = traceback.extract_tb(err.__traceback__)[-1]
            current_app.logger.error(
                "MEMOVS: error processing record %s: %s (at %s:%s in %s())",
                record_id,
                err,
                frame.filename,
                frame.lineno,
                frame.name,
            )
            return record_id, HarvestActionType.ERROR

    def harvest_records(self, from_date):
        """Harvest Memovs records.

        :param from_date: record changed after this date to get
        :returns: count and total items
        """
        self._count = 0
        url = self.get_request_url(start_date=from_date, page=1)
        request = self.session.get(url)

        if request.status_code != requests_codes.ok:
            self.verbose_print(f"Error fetching data: {request.status_code}")
            return self._count, 0

        response_data = request.json()
        total_pages = response_data.get("totalPages", 0)
        total_items = response_data.get("totalDocuments", 0)
        current_page = response_data.get("currentPage", 1)

        if self.process:
            self._build_caches()

        while (
            request.status_code == requests_codes.ok
            and current_page <= total_pages
            and (self.harvest_count < 0 or self._count < self.harvest_count)
        ):
            self.verbose_print(f"API page: {current_page}/{total_pages} url: {url}")
            self.process_records(response_data.get("documents", []))

            # Get next page
            current_page += 1
            if current_page <= total_pages:
                url = self.get_request_url(start_date=from_date, page=current_page)
                request = self.session.get(url)
                if request.status_code == requests_codes.ok:
                    response_data = request.json()

        return self._count, total_items

    def get_all_remote_ids(self):
        """Fetch every record ID currently published by the Memovs API.

        Uses start_date=1990-01-01 to retrieve the full catalogue.

        :returns: tuple ``(remote_ids, complete)``. ``remote_ids`` is the set
            of harvested ID strings (e.g. ``{'(MEMOVS)75864', …}``); ``complete``
            is True only when every page was fetched successfully. A partial
            crawl (any page failing) returns ``complete=False`` so the caller
            can refuse destructive operations rather than treat an incomplete
            set as authoritative.
        """
        remote_ids = set()
        url = self.get_request_url(start_date="1990-01-01", page=1)
        request = self.session.get(url)

        if request.status_code != requests_codes.ok:
            self.verbose_print(f"{self._vendor}: error fetching remote IDs: {request.status_code}")
            return remote_ids, False

        response_data = request.json()
        total_pages = response_data.get("totalPages", 0)
        current_page = response_data.get("currentPage", 1)

        while current_page <= total_pages:
            self.verbose_print(f"{self._vendor}: collecting IDs page {current_page}/{total_pages}")
            for record in response_data.get("documents", []):
                if at_id := record.get("@id", ""):
                    memovs_id = at_id.split(":")[-1] if ":" in at_id else at_id
                    if memovs_id:
                        remote_ids.add(f"(MEMOVS){memovs_id}")
            current_page += 1
            if current_page <= total_pages:
                url = self.get_request_url(start_date="1990-01-01", page=current_page)
                request = self.session.get(url)
                if request.status_code != requests_codes.ok:
                    self.verbose_print(
                        f"{self._vendor}: error fetching IDs page {current_page}: "
                        f"{request.status_code} — catalogue crawl incomplete"
                    )
                    return remote_ids, False
                response_data = request.json()

        return remote_ids, True

    def delete_orphan_records(self):
        """Delete RERO-ILS documents that no longer exist in the Memovs API.

        Fetches the full set of IDs from the Memovs API, then scans RERO-ILS
        for documents harvested from MEMOVS that are absent from that set.
        For each orphan, items are deleted first (holdings and local fields are
        cascade-deleted automatically). Documents that cannot be deleted due to
        active loans or fees are left intact.

        :returns: tuple of (deleted_count, can_not_delete_count).
        """
        remote_ids, complete = self.get_all_remote_ids()
        if not complete:
            self.verbose_print(
                f"{self._vendor}: incomplete catalogue crawl — aborting orphan deletion to avoid data loss"
            )
            return 0, 0
        if not remote_ids:
            self.verbose_print(f"{self._vendor}: no remote IDs returned — aborting orphan deletion to avoid data loss")
            return 0, 0

        deleted = 0
        can_not_delete = 0

        for hit in (
            DocumentsSearch().filter("term", identifiedBy__source=self._vendor).source(["pid", "identifiedBy"]).scan()
        ):
            hit_dict = hit.to_dict()
            harvested_id = next(
                (ident["value"] for ident in hit_dict.get("identifiedBy") or [] if ident.get("source") == self._vendor),
                None,
            )
            if not harvested_id or harvested_id in remote_ids:
                continue

            doc = Document.get_record_by_pid(hit_dict["pid"])
            if not doc:
                continue

            self.verbose_print(f"{self._vendor}: orphan {harvested_id} doc:{doc.pid} — attempting delete")
            self.delete_items(document_pid=doc.pid)
            doc.pop("harvested", None)
            if reasons := doc.reasons_not_to_delete():
                # Restore the in-memory flag; the popped value was never
                # persisted, so the ES index still reflects harvested=True and
                # no reindex is needed.
                doc["harvested"] = True
                doc.commit()
                can_not_delete += 1
                self.verbose_print(f"{self._vendor}: cannot delete {harvested_id} doc:{doc.pid}: {reasons}")
            else:
                doc.delete(dbcommit=True, delindex=True)
                deleted += 1

        return deleted, can_not_delete
