# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test ApiMemovs helper methods."""

from unittest.mock import MagicMock, patch

from rero_ils.modules.api_harvester.memovs.api import ApiMemovs
from rero_ils.modules.api_harvester.models import HarvestActionType

_LOCATION_PATCH = "rero_ils.modules.api_harvester.memovs.api.Location.get_record_by_pid"
_GET_LOFIS_PATCH = "rero_ils.modules.api_harvester.memovs.api.LocalField.get_local_fields_by_id"
_CREATE_PATCH = "rero_ils.modules.api_harvester.memovs.api.LocalField.create"
_LOGGER_PATCH = "rero_ils.modules.api_harvester.memovs.api.current_app"
_LOFI_GET_PATCH = "rero_ils.modules.api_harvester.memovs.api.LocalField.get_record_by_pid"
_ITEM_GET_PATCH = "rero_ils.modules.api_harvester.memovs.api.Item.get_record_by_pid"
_ITEM_CREATE_PATCH = "rero_ils.modules.api_harvester.memovs.api.Item.create"
_DOC_GET_PATCH = "rero_ils.modules.api_harvester.memovs.api.Document.get_record_by_pid"
_DOC_CREATE_PATCH = "rero_ils.modules.api_harvester.memovs.api.Document.create"
_MEMOVS_JSON_PATCH = "rero_ils.modules.api_harvester.memovs.api.memovs_json"
_REQUESTS_PATCH = "rero_ils.modules.api_harvester.memovs.api.requests_retry_session"
_ILS_INDEXER_PATCH = "rero_ils.modules.api_harvester.memovs.api.IlsRecordsIndexer"
_HOLDING_PATCH = "rero_ils.modules.api_harvester.memovs.api.Holding"
_EXTRACTED_REF_PATCH = "rero_ils.modules.api_harvester.memovs.api.extracted_data_from_ref"


def _make_harvester(settings):
    """Return an ApiMemovs instance with a mocked config, bypassing __init__."""
    harvester = ApiMemovs.__new__(ApiMemovs)
    harvester.config = MagicMock()
    harvester.config.settings = settings
    return harvester


def _mock_location(org_pid):
    """Return a mock Location whose organisation_pid is org_pid."""
    loc = MagicMock()
    loc.organisation_pid = org_pid
    return loc


def test_extract_local_fields():
    """Test _extract_local_fields keeps only vsavmat/vsavgeo/vsavfonds notes."""
    # Only the local-field note types are kept; general notes are excluded
    data = {
        "bf:note": [
            {"bf:noteType": "vsavgeo", "rdfs:label": "geo label"},
            {"bf:noteType": "vsavmat", "rdfs:label": "mat label"},
            {"bf:noteType": "vsavfonds", "rdfs:label": "fonds label"},
            {"bf:noteType": "general", "rdfs:label": "a general note"},
        ]
    }
    assert ApiMemovs._extract_local_fields(data) == ["geo label", "mat label", "fonds label"]

    # noteType match is case-insensitive
    assert ApiMemovs._extract_local_fields({"bf:note": [{"bf:noteType": "VsavGeo", "rdfs:label": "geo"}]}) == ["geo"]

    # a matching noteType with an empty label is skipped
    assert ApiMemovs._extract_local_fields({"bf:note": [{"bf:noteType": "vsavgeo", "rdfs:label": ""}]}) == []

    # a note without a recognised noteType is skipped
    assert ApiMemovs._extract_local_fields({"bf:note": [{"bf:noteType": "", "rdfs:label": "x"}]}) == []

    # No bf:note key
    assert ApiMemovs._extract_local_fields({}) == []


def test_sync_local_field_create(app):
    """Create a local field when none exists for the document."""
    harvester = _make_harvester({"location_pid": "loc1", "local_field_name": "field_1"})
    local_fields = ["$2 vsavgeo $a chvs-0 $d Valais"]

    with (
        patch(_LOCATION_PATCH, return_value=_mock_location("org2")),
        patch(_GET_LOFIS_PATCH, return_value=iter([])),
        patch(_CREATE_PATCH) as mock_create,
    ):
        harvester.sync_local_field(document_pid="doc1", local_fields=local_fields)

    mock_create.assert_called_once()
    created_data = mock_create.call_args.kwargs["data"]
    assert created_data["fields"] == {"field_1": local_fields}
    assert "doc1" in created_data["parent"]["$ref"]
    assert "org2" in created_data["organisation"]["$ref"]
    assert mock_create.call_args.kwargs["dbcommit"] is True
    assert mock_create.call_args.kwargs["reindex"] is True


def test_sync_local_field_create_custom_field_name(app):
    """Respect the local_field_name setting when creating."""
    harvester = _make_harvester({"location_pid": "loc1", "local_field_name": "field_3"})
    local_fields = ["some note"]

    with (
        patch(_LOCATION_PATCH, return_value=_mock_location("org2")),
        patch(_GET_LOFIS_PATCH, return_value=iter([])),
        patch(_CREATE_PATCH) as mock_create,
    ):
        harvester.sync_local_field(document_pid="doc1", local_fields=local_fields)

    created_data = mock_create.call_args.kwargs["data"]
    assert "field_3" in created_data["fields"]


def test_sync_local_field_no_location(app):
    """Omit organisation from the local field when location_pid is absent."""
    harvester = _make_harvester({})
    local_fields = ["some note"]

    with patch(_GET_LOFIS_PATCH, return_value=iter([])), patch(_CREATE_PATCH) as mock_create:
        harvester.sync_local_field(document_pid="doc1", local_fields=local_fields)

    created_data = mock_create.call_args.kwargs["data"]
    assert "organisation" not in created_data


def test_sync_local_field_update(app):
    """Replace the existing local field when one already exists."""
    harvester = _make_harvester({"location_pid": "loc1"})
    local_fields = ["updated note"]
    existing = MagicMock()
    existing.pid = "lofi99"

    with (
        patch(_LOCATION_PATCH, return_value=_mock_location("org2")),
        patch(_GET_LOFIS_PATCH, return_value=iter([existing])),
        patch(_CREATE_PATCH) as mock_create,
    ):
        changed = harvester.sync_local_field(document_pid="doc1", local_fields=local_fields)

    mock_create.assert_not_called()
    existing.replace.assert_called_once()
    replaced_data = existing.replace.call_args.kwargs["data"]
    assert replaced_data["pid"] == "lofi99"
    assert replaced_data["fields"] == {"field_2": local_fields}
    assert changed is True


def test_sync_local_field_skip_when_unchanged(app):
    """Leave the existing local field untouched when its fields already match."""
    harvester = _make_harvester({"location_pid": "loc1"})
    local_fields = ["unchanged note"]
    existing = MagicMock()
    existing.pid = "lofi99"
    existing.get.return_value = {"field_2": local_fields}

    with (
        patch(_LOCATION_PATCH, return_value=_mock_location("org2")),
        patch(_GET_LOFIS_PATCH, return_value=iter([existing])),
        patch(_CREATE_PATCH) as mock_create,
    ):
        changed = harvester.sync_local_field(document_pid="doc1", local_fields=local_fields)

    mock_create.assert_not_called()
    existing.replace.assert_not_called()
    assert changed is False


def test_sync_local_field_delete_existing(app):
    """Delete the existing local field when notes become empty."""
    harvester = _make_harvester({"location_pid": "loc1"})
    existing = MagicMock()

    with (
        patch(_LOCATION_PATCH, return_value=_mock_location("org2")),
        patch(_GET_LOFIS_PATCH, return_value=iter([existing])),
        patch(_CREATE_PATCH) as mock_create,
    ):
        harvester.sync_local_field(document_pid="doc1", local_fields=[])

    existing.delete.assert_called_once_with(dbcommit=True, delindex=True)
    mock_create.assert_not_called()


def test_sync_local_field_noop_when_empty_and_none_exist(app):
    """Do nothing when notes are empty and no local field exists."""
    harvester = _make_harvester({})

    with patch(_GET_LOFIS_PATCH, return_value=iter([])), patch(_CREATE_PATCH) as mock_create:
        harvester.sync_local_field(document_pid="doc1", local_fields=[])

    mock_create.assert_not_called()


def test_sync_local_field_skip_when_location_not_found(app):
    """Skip and log a warning when location_pid is set but the location does not exist."""
    harvester = _make_harvester({"location_pid": "missing-loc"})
    local_fields = ["some note"]

    with (
        patch(_LOCATION_PATCH, return_value=None),
        patch(_CREATE_PATCH) as mock_create,
        patch(_LOGGER_PATCH) as mock_app,
    ):
        harvester.sync_local_field(document_pid="doc1", local_fields=local_fields)

    mock_create.assert_not_called()
    mock_app.logger.warning.assert_called_once()
    assert "missing-loc" in mock_app.logger.warning.call_args.args[0]


# ---------------------------------------------------------------------------
# get_request_url
# ---------------------------------------------------------------------------


def test_get_request_url():
    """Test that get_request_url builds the expected query string."""
    harvester = _make_harvester({})
    harvester._url = "https://api.memovs.ch/records"

    assert harvester.get_request_url() == "https://api.memovs.ch/records?from=1990-01-01&currentPage=1"
    assert harvester.get_request_url(start_date="2024-01-01", page=3) == (
        "https://api.memovs.ch/records?from=2024-01-01&currentPage=3"
    )


# ---------------------------------------------------------------------------
# msg_text
# ---------------------------------------------------------------------------


def test_msg_text():
    """Test msg_text appends doc pid when _last_doc_pid is set."""
    harvester = _make_harvester({})
    harvester._vendor = "MEMOVS"
    harvester._code = "memovs"
    harvester._count = 5
    harvester._last_doc_pid = None

    base = harvester.msg_text(pid="(MEMOVS)123", msg="created")
    assert "doc:" not in base

    harvester._last_doc_pid = "doc42"
    with_doc = harvester.msg_text(pid="(MEMOVS)123", msg="created")
    assert "doc:doc42" in with_doc


# ---------------------------------------------------------------------------
# _extract_call_number
# ---------------------------------------------------------------------------


def test_extract_call_number():
    """Test _extract_call_number returns the rdf:value from the first matching identifier."""
    part = {"bf:identifier": [{"rdf:value": "037ph-00038a-h"}, {"rdf:value": "ignored"}]}
    assert ApiMemovs._extract_call_number(part) == "037ph-00038a-h"

    # No identifier list — returns empty string
    assert ApiMemovs._extract_call_number({}) == ""

    # Identifier present but no rdf:value
    assert ApiMemovs._extract_call_number({"bf:identifier": [{}]}) == ""


# ---------------------------------------------------------------------------
# delete_items
# ---------------------------------------------------------------------------


def test_delete_items_no_settings():
    """delete_items returns immediately when location_pid or item_type_pid is missing."""
    harvester = _make_harvester({})
    harvester._items_cache = {}
    with patch(_ITEM_GET_PATCH) as mock_get:
        harvester.delete_items("doc1")
    mock_get.assert_not_called()


def test_delete_items_from_cache():
    """delete_items uses cached pids and calls delete on each item."""
    harvester = _make_harvester({"location_pid": "loc1", "item_type_pid": "itty1"})
    item_mock = MagicMock()
    harvester._items_cache = {"doc1": {"call_A": "item1", "call_B": "item2"}}

    with patch(_ITEM_GET_PATCH, return_value=item_mock) as mock_get:
        harvester.delete_items("doc1")

    assert mock_get.call_count == 2
    assert item_mock.delete.call_count == 2
    item_mock.delete.assert_called_with(dbcommit=True, delindex=True)
    # Cache entry should be removed
    assert "doc1" not in harvester._items_cache


def test_delete_items_item_not_found():
    """delete_items silently skips when an item pid no longer exists."""
    harvester = _make_harvester({"location_pid": "loc1", "item_type_pid": "itty1"})
    harvester._items_cache = {"doc1": {"call_A": "item1"}}

    with patch(_ITEM_GET_PATCH, return_value=None):
        harvester.delete_items("doc1")  # should not raise


# ---------------------------------------------------------------------------
# sync_items
# ---------------------------------------------------------------------------


def test_sync_items_no_settings():
    """sync_items returns immediately when location_pid or item_type_pid is missing."""
    harvester = _make_harvester({})
    harvester._items_cache = {}
    with patch(_ITEM_CREATE_PATCH) as mock_create:
        harvester.sync_items("doc1", [])
    mock_create.assert_not_called()


def test_sync_items_new_call_number():
    """sync_items creates an item for each new call number not yet in the cache."""
    harvester = _make_harvester({"location_pid": "loc1", "item_type_pid": "itty1"})
    harvester._items_cache = {}

    has_parts = [{"bf:identifier": [{"rdf:value": "CALL-001"}]}]
    new_item = MagicMock()
    new_item.pid = "item99"

    with (
        patch(_ITEM_CREATE_PATCH, return_value=new_item) as mock_create,
        patch(_EXTRACTED_REF_PATCH, return_value="hold1"),
        patch(_ILS_INDEXER_PATCH),
        patch(_HOLDING_PATCH),
    ):
        harvester.sync_items("doc1", has_parts)

    mock_create.assert_called_once()
    created_data = mock_create.call_args.kwargs["data"]
    assert created_data["call_number"] == "CALL-001"
    assert "loc1" in created_data["location"]["$ref"]
    assert harvester._items_cache["doc1"]["CALL-001"] == "item99"


def test_sync_items_delete_stale():
    """sync_items deletes items whose call number is no longer in has_parts."""
    harvester = _make_harvester({"location_pid": "loc1", "item_type_pid": "itty1"})
    harvester._items_cache = {"doc1": {"OLD-001": "item_old"}}

    stale_item = MagicMock()
    has_parts = [{"bf:identifier": [{"rdf:value": "NEW-001"}]}]
    new_item = MagicMock()
    new_item.pid = "item_new"

    with (
        patch(_ITEM_GET_PATCH, return_value=stale_item),
        patch(_ITEM_CREATE_PATCH, return_value=new_item),
        patch(_EXTRACTED_REF_PATCH, return_value="hold1"),
        patch(_ILS_INDEXER_PATCH),
        patch(_HOLDING_PATCH),
    ):
        harvester.sync_items("doc1", has_parts)

    stale_item.delete.assert_called_once_with(dbcommit=True, delindex=True)
    assert "NEW-001" in harvester._items_cache["doc1"]
    assert "OLD-001" not in harvester._items_cache["doc1"]


def test_sync_items_url_fallback():
    """sync_items uses the last URL path segment as call_number when has_parts is empty."""
    harvester = _make_harvester({"location_pid": "loc1", "item_type_pid": "itty1"})
    harvester._items_cache = {}
    new_item = MagicMock()
    new_item.pid = "item1"

    with (
        patch(_ITEM_CREATE_PATCH, return_value=new_item) as mock_create,
        patch(_EXTRACTED_REF_PATCH, return_value="hold1"),
        patch(_ILS_INDEXER_PATCH),
        patch(_HOLDING_PATCH),
    ):
        harvester.sync_items("doc1", [], url="https://archives.memovs.ch/detail/urn:avn:12345")

    mock_create.assert_called_once()
    created_data = mock_create.call_args.kwargs["data"]
    assert created_data["call_number"] == "urn:avn:12345"


def test_sync_items_existing_unchanged():
    """sync_items leaves items untouched when the call number already exists."""
    harvester = _make_harvester({"location_pid": "loc1", "item_type_pid": "itty1"})
    harvester._items_cache = {"doc1": {"CALL-001": "item_existing"}}

    has_parts = [{"bf:identifier": [{"rdf:value": "CALL-001"}]}]

    with patch(_ITEM_CREATE_PATCH) as mock_create, patch(_ITEM_GET_PATCH) as mock_get:
        changed = harvester.sync_items("doc1", has_parts)

    mock_create.assert_not_called()
    mock_get.assert_not_called()
    assert harvester._items_cache["doc1"]["CALL-001"] == "item_existing"
    assert changed is False


# ---------------------------------------------------------------------------
# sync_local_field — cache mode
# ---------------------------------------------------------------------------


def test_sync_local_field_cache_mode_create(app):
    """Create a local field in cache mode when none exists."""
    harvester = _make_harvester({"location_pid": "loc1", "local_field_name": "field_2"})
    harvester._lofis_cache = {}
    harvester._cached_org_pid = "org1"
    local_fields = ["note A"]

    new_lofi = MagicMock()
    new_lofi.pid = "lofi_new"

    with patch(_LOFI_GET_PATCH, return_value=None), patch(_CREATE_PATCH, return_value=new_lofi) as mock_create:
        harvester.sync_local_field(document_pid="doc1", local_fields=local_fields)

    mock_create.assert_called_once()
    assert harvester._lofis_cache["doc1"] == "lofi_new"


def test_sync_local_field_cache_mode_update(app):
    """Update an existing local field in cache mode."""
    harvester = _make_harvester({"location_pid": "loc1"})
    harvester._lofis_cache = {"doc1": "lofi_old"}
    harvester._cached_org_pid = "org1"
    local_fields = ["updated note"]

    existing = MagicMock()
    existing.pid = "lofi_old"

    with patch(_LOFI_GET_PATCH, return_value=existing), patch(_CREATE_PATCH) as mock_create:
        harvester.sync_local_field(document_pid="doc1", local_fields=local_fields)

    mock_create.assert_not_called()
    existing.replace.assert_called_once()
    replaced = existing.replace.call_args.kwargs["data"]
    assert replaced["pid"] == "lofi_old"


def test_sync_local_field_cache_mode_delete(app):
    """Delete an existing local field in cache mode when notes become empty."""
    harvester = _make_harvester({"location_pid": "loc1"})
    harvester._lofis_cache = {"doc1": "lofi_old"}
    harvester._cached_org_pid = "org1"

    existing = MagicMock()

    with patch(_LOFI_GET_PATCH, return_value=existing):
        harvester.sync_local_field(document_pid="doc1", local_fields=[])

    existing.delete.assert_called_once_with(dbcommit=True, delindex=True)
    assert "doc1" not in harvester._lofis_cache


# ---------------------------------------------------------------------------
# create_update_record
# ---------------------------------------------------------------------------


def _make_full_harvester(settings=None):
    """Return ApiMemovs with all internal state needed by create_update_record."""
    harvester = _make_harvester(settings or {})
    harvester._vendor = "MEMOVS"
    harvester._code = "memovs"
    harvester._url = "https://api.memovs.ch/records"
    harvester._count = 0
    harvester._count_new = 0
    harvester._count_upd = 0
    harvester._count_del = 0
    harvester._count_unchanged = 0
    harvester._existing_docs = {}
    harvester._items_cache = {}
    harvester._lofis_cache = {}
    harvester._cached_org_pid = "org1"
    harvester._last_doc_pid = None
    harvester.verbose = False
    harvester.harvest_count = -1
    harvester.process = False
    return harvester


def test_create_update_record_creates_new(app):
    """create_update_record creates a document when the harvested ID is new."""
    harvester = _make_full_harvester()
    record = {"@id": "urn:avn:111"}
    record_data = {"pid": "(MEMOVS)111", "$schema": "doc_schema", "harvested": True}

    new_doc = MagicMock()
    new_doc.pid = "doc_created"

    with (
        patch(_MEMOVS_JSON_PATCH) as mock_trans,
        patch(_DOC_CREATE_PATCH, return_value=new_doc) as mock_doc_create,
        patch.object(harvester, "sync_items"),
        patch.object(harvester, "sync_local_field"),
    ):
        mock_trans.do.return_value = dict(record_data)
        harvested_id, status = harvester.create_update_record(record)

    assert harvested_id == "(MEMOVS)111"
    assert status == HarvestActionType.CREATED
    mock_doc_create.assert_called_once()
    assert harvester._existing_docs["(MEMOVS)111"] == "doc_created"
    assert harvester._count_new == 1


def test_create_update_record_updates_existing(app):
    """create_update_record updates a document when the harvested ID already exists."""
    harvester = _make_full_harvester()
    harvester._existing_docs["(MEMOVS)222"] = "doc_old"
    record = {"@id": "urn:avn:222"}
    record_data = {"pid": "(MEMOVS)222", "$schema": "doc_schema"}

    existing_doc = MagicMock()
    existing_doc.pid = "doc_old"
    updated_doc = MagicMock()
    updated_doc.pid = "doc_old"

    with (
        patch(_MEMOVS_JSON_PATCH) as mock_trans,
        patch(_DOC_GET_PATCH, return_value=existing_doc),
        patch.object(harvester, "sync_items"),
        patch.object(harvester, "sync_local_field"),
    ):
        mock_trans.do.return_value = dict(record_data)
        existing_doc.replace.return_value = updated_doc
        harvested_id, status = harvester.create_update_record(record)

    assert status == HarvestActionType.UPDATED
    existing_doc.replace.assert_called_once()
    assert harvester._count_upd == 1


def test_create_update_record_unchanged(app):
    """create_update_record reports UNCHANGED when doc, items and local field are unchanged."""
    harvester = _make_full_harvester()
    harvester._existing_docs["(MEMOVS)222"] = "doc_old"
    record = {"@id": "urn:avn:222"}
    record_data = {"pid": "(MEMOVS)222", "$schema": "doc_schema"}

    existing_doc = MagicMock()
    existing_doc.pid = "doc_old"

    with (
        patch(_MEMOVS_JSON_PATCH) as mock_trans,
        patch(_DOC_GET_PATCH, return_value=existing_doc),
        patch.object(harvester, "_document_differs", return_value=False),
        patch.object(harvester, "sync_items", return_value=False),
        patch.object(harvester, "sync_local_field", return_value=False),
    ):
        mock_trans.do.return_value = dict(record_data)
        _, status = harvester.create_update_record(record)

    # nothing changed: the document is not replaced/reindexed and the status is UNCHANGED
    existing_doc.replace.assert_not_called()
    assert status == HarvestActionType.UNCHANGED
    assert harvester._count_unchanged == 1
    assert harvester._count_upd == 0


def test_create_update_record_deletes_existing(app):
    """create_update_record deletes a document when the record is flagged deleted."""
    harvester = _make_full_harvester()
    harvester._existing_docs["(MEMOVS)333"] = "doc_del"
    record = {"@id": "urn:avn:333"}
    record_data = {"pid": "(MEMOVS)333", "deleted": True}

    existing_doc = MagicMock()
    existing_doc.pid = "doc_del"
    existing_doc.reasons_not_to_delete.return_value = []

    with (
        patch(_MEMOVS_JSON_PATCH) as mock_trans,
        patch(_DOC_GET_PATCH, return_value=existing_doc),
        patch.object(harvester, "delete_items"),
    ):
        mock_trans.do.return_value = dict(record_data)
        harvested_id, status = harvester.create_update_record(record)

    assert status == HarvestActionType.DELETED
    existing_doc.delete.assert_called_once_with(dbcommit=True, delindex=True)
    assert "(MEMOVS)333" not in harvester._existing_docs
    assert harvester._count_del == 1


def test_create_update_record_skip_deleted_without_pid(app):
    """create_update_record does nothing for a deleted record with no existing pid."""
    harvester = _make_full_harvester()
    record = {"@id": "urn:avn:444"}
    record_data = {"pid": "(MEMOVS)444", "deleted": True}

    with (
        patch(_MEMOVS_JSON_PATCH) as mock_trans,
        patch(_DOC_CREATE_PATCH) as mock_doc_create,
    ):
        mock_trans.do.return_value = dict(record_data)
        harvested_id, status = harvester.create_update_record(record)

    mock_doc_create.assert_not_called()
    assert status == HarvestActionType.DELETED


# ---------------------------------------------------------------------------
# harvest_records
# ---------------------------------------------------------------------------


def _mock_response(status_code=200, json_data=None):
    """Return a mock requests.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    return resp


def test_harvest_records_http_error(app):
    """harvest_records returns (0, 0) when the first request fails."""
    harvester = _make_full_harvester()
    harvester._url = "https://api.memovs.ch/records"
    harvester._count = 0
    harvester.process = False

    session = MagicMock()
    session.get.return_value = _mock_response(status_code=500)

    with patch(_REQUESTS_PATCH, return_value=session):
        count, total = harvester.harvest_records("2024-01-01")

    assert count == 0
    assert total == 0


def test_harvest_records_single_page(app):
    """harvest_records processes a single-page response without crashing."""
    harvester = _make_full_harvester()
    harvester._url = "https://api.memovs.ch/records"
    harvester._count = 0
    harvester.process = False

    page_data = {
        "totalPages": 1,
        "totalDocuments": 2,
        "currentPage": 1,
        "documents": [{"@id": "urn:avn:1"}, {"@id": "urn:avn:2"}],
    }
    session = MagicMock()
    session.get.return_value = _mock_response(json_data=page_data)

    with (
        patch(_REQUESTS_PATCH, return_value=session),
        patch.object(harvester, "process_records") as mock_proc,
    ):
        count, total = harvester.harvest_records("2024-01-01")

    mock_proc.assert_called_once_with(page_data["documents"])
    assert total == 2


# ---------------------------------------------------------------------------
# get_all_remote_ids
# ---------------------------------------------------------------------------


def test_get_all_remote_ids_http_error():
    """get_all_remote_ids returns an empty set and complete=False when the first request fails."""
    harvester = _make_full_harvester()
    harvester._url = "https://api.memovs.ch/records"
    harvester._vendor = "MEMOVS"

    session = MagicMock()
    session.get.return_value = _mock_response(status_code=500)

    with patch(_REQUESTS_PATCH, return_value=session):
        ids, complete = harvester.get_all_remote_ids()

    assert ids == set()
    assert complete is False


def test_get_all_remote_ids_single_page():
    """get_all_remote_ids collects IDs from a single-page response and reports complete."""
    harvester = _make_full_harvester()
    harvester._url = "https://api.memovs.ch/records"
    harvester._vendor = "MEMOVS"

    page = {
        "totalPages": 1,
        "currentPage": 1,
        "documents": [
            {"@id": "urn:avn:111"},
            {"@id": "urn:avn:222"},
            {"@id": "urn:avn:333"},
        ],
    }
    session = MagicMock()
    session.get.return_value = _mock_response(json_data=page)

    with patch(_REQUESTS_PATCH, return_value=session):
        ids, complete = harvester.get_all_remote_ids()

    assert ids == {"(MEMOVS)111", "(MEMOVS)222", "(MEMOVS)333"}
    assert complete is True


def test_get_all_remote_ids_multi_page():
    """get_all_remote_ids paginates and collects IDs across all pages."""
    harvester = _make_full_harvester()
    harvester._url = "https://api.memovs.ch/records"
    harvester._vendor = "MEMOVS"

    page1 = {"totalPages": 2, "currentPage": 1, "documents": [{"@id": "urn:avn:1"}, {"@id": "urn:avn:2"}]}
    page2 = {"totalPages": 2, "currentPage": 2, "documents": [{"@id": "urn:avn:3"}]}

    session = MagicMock()
    session.get.side_effect = [_mock_response(json_data=page1), _mock_response(json_data=page2)]

    with patch(_REQUESTS_PATCH, return_value=session):
        ids, complete = harvester.get_all_remote_ids()

    assert ids == {"(MEMOVS)1", "(MEMOVS)2", "(MEMOVS)3"}
    assert complete is True
    assert session.get.call_count == 2


def test_get_all_remote_ids_partial_crawl():
    """A page failing mid-crawl returns the partial set with complete=False."""
    harvester = _make_full_harvester()
    harvester._url = "https://api.memovs.ch/records"
    harvester._vendor = "MEMOVS"

    page1 = {"totalPages": 3, "currentPage": 1, "documents": [{"@id": "urn:avn:1"}, {"@id": "urn:avn:2"}]}

    session = MagicMock()
    # page 1 ok, page 2 fails -> crawl aborts as incomplete
    session.get.side_effect = [_mock_response(json_data=page1), _mock_response(status_code=503)]

    with patch(_REQUESTS_PATCH, return_value=session):
        ids, complete = harvester.get_all_remote_ids()

    assert ids == {"(MEMOVS)1", "(MEMOVS)2"}
    assert complete is False


def test_get_all_remote_ids_skips_missing_at_id():
    """get_all_remote_ids silently skips records without an @id field."""
    harvester = _make_full_harvester()
    harvester._url = "https://api.memovs.ch/records"
    harvester._vendor = "MEMOVS"

    page = {
        "totalPages": 1,
        "currentPage": 1,
        "documents": [{"@id": "urn:avn:10"}, {}, {"bf:title": "no id here"}],
    }
    session = MagicMock()
    session.get.return_value = _mock_response(json_data=page)

    with patch(_REQUESTS_PATCH, return_value=session):
        ids, complete = harvester.get_all_remote_ids()

    assert ids == {"(MEMOVS)10"}
    assert complete is True


# ---------------------------------------------------------------------------
# delete_orphan_records
# ---------------------------------------------------------------------------

_DOC_SEARCH_PATCH = "rero_ils.modules.api_harvester.memovs.api.DocumentsSearch"


def _mock_es_hit(doc_pid, memovs_id):
    """Return a mock ES hit representing a harvested document."""
    hit = MagicMock()
    hit.to_dict.return_value = {
        "pid": doc_pid,
        "identifiedBy": [{"source": "MEMOVS", "value": memovs_id}],
    }
    return hit


def test_delete_orphan_records_aborts_on_empty_remote(app):
    """delete_orphan_records aborts without touching RERO-ILS when remote returns no IDs."""
    harvester = _make_full_harvester()
    harvester._vendor = "MEMOVS"

    with (
        patch.object(harvester, "get_all_remote_ids", return_value=(set(), True)),
        patch(_DOC_SEARCH_PATCH) as mock_search,
    ):
        deleted, can_not_delete = harvester.delete_orphan_records()

    assert deleted == 0
    assert can_not_delete == 0
    mock_search.assert_not_called()


def test_delete_orphan_records_aborts_on_incomplete_crawl(app):
    """delete_orphan_records refuses to delete when the catalogue crawl was incomplete."""
    harvester = _make_full_harvester()
    harvester._vendor = "MEMOVS"

    # A non-empty but partial set must NOT be treated as authoritative.
    with (
        patch.object(harvester, "get_all_remote_ids", return_value=({"(MEMOVS)111"}, False)),
        patch(_DOC_SEARCH_PATCH) as mock_search,
    ):
        deleted, can_not_delete = harvester.delete_orphan_records()

    assert deleted == 0
    assert can_not_delete == 0
    mock_search.assert_not_called()


def test_delete_orphan_records_skips_still_remote(app):
    """delete_orphan_records leaves documents alone when their ID is still in the remote set."""
    harvester = _make_full_harvester()
    harvester._vendor = "MEMOVS"
    harvester._items_cache = {}

    hit = _mock_es_hit("doc1", "(MEMOVS)111")

    with (
        patch.object(harvester, "get_all_remote_ids", return_value=({"(MEMOVS)111", "(MEMOVS)222"}, True)),
        patch(_DOC_SEARCH_PATCH) as mock_search,
        patch(_DOC_GET_PATCH) as mock_doc_get,
    ):
        mock_search.return_value.filter.return_value.source.return_value.scan.return_value = [hit]
        deleted, can_not_delete = harvester.delete_orphan_records()

    assert deleted == 0
    assert can_not_delete == 0
    mock_doc_get.assert_not_called()


def test_delete_orphan_records_deletes_orphan(app):
    """delete_orphan_records deletes a document that is absent from the remote set."""
    harvester = _make_full_harvester()
    harvester._vendor = "MEMOVS"
    harvester._items_cache = {}

    hit = _mock_es_hit("doc1", "(MEMOVS)999")
    doc = MagicMock()
    doc.pid = "doc1"
    doc.reasons_not_to_delete.return_value = {}

    with (
        patch.object(harvester, "get_all_remote_ids", return_value=({"(MEMOVS)111"}, True)),
        patch(_DOC_SEARCH_PATCH) as mock_search,
        patch(_DOC_GET_PATCH, return_value=doc),
        patch.object(harvester, "delete_items") as mock_del_items,
    ):
        mock_search.return_value.filter.return_value.source.return_value.scan.return_value = [hit]
        deleted, can_not_delete = harvester.delete_orphan_records()

    assert deleted == 1
    assert can_not_delete == 0
    mock_del_items.assert_called_once_with(document_pid="doc1")
    doc.pop.assert_called_once_with("harvested", None)
    doc.delete.assert_called_once_with(dbcommit=True, delindex=True)


def test_delete_orphan_records_counts_cannot_delete(app):
    """delete_orphan_records counts documents that have active loans and cannot be deleted."""
    harvester = _make_full_harvester()
    harvester._vendor = "MEMOVS"
    harvester._items_cache = {}

    hit = _mock_es_hit("doc1", "(MEMOVS)999")
    doc = MagicMock()
    doc.pid = "doc1"
    doc.reasons_not_to_delete.return_value = {"links": {"loans": 2}}

    with (
        patch.object(harvester, "get_all_remote_ids", return_value=({"(MEMOVS)111"}, True)),
        patch(_DOC_SEARCH_PATCH) as mock_search,
        patch(_DOC_GET_PATCH, return_value=doc),
        patch.object(harvester, "delete_items"),
    ):
        mock_search.return_value.filter.return_value.source.return_value.scan.return_value = [hit]
        deleted, can_not_delete = harvester.delete_orphan_records()

    assert deleted == 0
    assert can_not_delete == 1
    doc.delete.assert_not_called()
    # harvested flag must be restored
    doc.__setitem__.assert_called_with("harvested", True)
    doc.commit.assert_called_once()
