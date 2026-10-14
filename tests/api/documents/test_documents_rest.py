# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests REST API documents."""

import json
from copy import deepcopy
from datetime import datetime, timedelta
from unittest import mock

import pytest
from flask import url_for
from invenio_accounts.testutils import login_user_via_session

from rero_ils.modules.commons.identifiers import IdentifierType
from rero_ils.modules.documents.api import Document, DocumentsSearch
from rero_ils.modules.files.cli import create_pdf_record_files
from rero_ils.modules.holdings.api import Holding, HoldingsSearch
from rero_ils.modules.items.api import Item, ItemsIndexer, ItemsSearch
from rero_ils.modules.items.tasks import clean_obsolete_temporary_item_types_and_locations
from rero_ils.modules.operation_logs.api import OperationLogsSearch
from rero_ils.modules.utils import get_ref_for_pid
from tests.utils import (
    VerifyRecordPermissionPatch,
    clean_text,
    get_json,
    mock_response,
    postdata,
    to_relative_url,
)


@mock.patch(
    "invenio_records_rest.views.verify_record_permission",
    mock.MagicMock(return_value=VerifyRecordPermissionPatch),
)
def test_documents_get(client, document_with_files):
    """Test record retrieval."""
    document = document_with_files

    def clean_search_metadata(metadata):
        """Clean contribution from authorized_access_point_."""
        # Contributions, subject and genreForm are i18n indexed field, so it's
        # too complicated to compare it from original record. Just take the
        # data from original record ... not best, but not real alternatives.
        if contribution := document.get("contribution"):
            metadata["contribution"] = contribution
        if subjects := document.get("subjects"):
            metadata["subjects"] = subjects
        if genreForms := document.get("genreForm"):
            metadata["genreForm"] = genreForms

        # REMOVE DYNAMICALLY ADDED search KEYS (see indexer.py:IndexerDumper)
        metadata.pop("sort_date_new", None)
        metadata.pop("sort_date_old", None)
        metadata.pop("sort_title", None)
        metadata.pop("isbn", None)
        metadata.pop("issn", None)
        metadata.pop("nested_identifiers", None)
        metadata.pop("identifiedBy", None)
        metadata.pop("files", None)
        metadata.pop("has_online_item", None)
        metadata.pop("has_physical_resources", None)
        return metadata

    item_url = url_for("invenio_records_rest.doc_item", pid_value="doc1")
    res = client.get(item_url)
    assert res.status_code == 200
    assert res.headers["ETag"] == f'"{document.revision_id}"'
    data = get_json(res)
    # DEV NOTES : Why removing `identifiedBy` key
    #   During the search enrichment process, we complete the original identifiers
    #   with alternate identifiers. So comparing search data identifiers, to
    #   original data identifiers doesn't make sense.
    document_data = document.dumps()
    document_data.pop("identifiedBy", None)
    assert document_data == clean_search_metadata(data["metadata"])

    # Check self links
    res = client.get(to_relative_url(data["links"]["self"]))
    assert res.status_code == 200
    res_content = get_json(res)
    res_content.get("metadata", {}).pop("identifiedBy", None)
    assert data == res_content
    document_data = document.dumps()
    document_data.pop("identifiedBy", None)
    assert document_data == clean_search_metadata(data["metadata"])

    list_url = url_for("invenio_records_rest.doc_list", q=f"pid:{document.pid}")
    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    metadata = data["hits"]["hits"][0]["metadata"]
    files = metadata["files"]
    assert len(files) == 2
    assert set(files[0].keys()) == {
        "file_name",
        "rec_id",
        "collections",
        "organisation_pid",
        "library_pid",
    }
    data_clean = clean_search_metadata(metadata)
    document = document.replace_refs().dumps()
    document.pop("identifiedBy", None)
    assert document == data_clean

    list_url = url_for("invenio_records_rest.doc_list", q="Vincent Berthe")
    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data["hits"]["total"] == 1


def test_documents_newacq_filters(
    app,
    client,
    system_librarian_martigny,
    rero_json_header,
    document,
    document_sion_items,
    export_document,
    holding_lib_martigny,
    holding_lib_saxon,
    loc_public_saxon,
    item_lib_martigny_data,
):
    """Test documents new acquisition filters."""
    login_user_via_session(client, system_librarian_martigny.user)

    def datetime_delta(**args):
        """Apply delta on date time."""
        return datetime.now() + timedelta(**args)

    def datetime_milliseconds(date):
        """Datetime get milliseconds."""
        return round(date.timestamp() * 1000)

    # compute useful date
    today = datetime.now()
    past = datetime_delta(days=-1).strftime("%Y-%m-%d")
    future = datetime_delta(days=10).strftime("%Y-%m-%d")
    future_1 = datetime_delta(days=11).strftime("%Y-%m-%d")
    acq_past_timestamp = datetime_milliseconds(datetime_delta(days=-30))
    acq_future_timestamp = datetime_milliseconds(datetime_delta(days=1))
    today = today.strftime("%Y-%m-%d")

    # add a new item with acq_date
    new_acq1 = deepcopy(item_lib_martigny_data)
    new_acq1["pid"] = "itemacq1"
    new_acq1["acquisition_date"] = today
    res, data = postdata(client, "invenio_records_rest.item_list", new_acq1)
    assert res.status_code == 201

    new_acq2 = deepcopy(item_lib_martigny_data)
    new_acq2["pid"] = "itemacq2"
    new_acq2["acquisition_date"] = future
    new_acq2["location"]["$ref"] = get_ref_for_pid("loc", loc_public_saxon.pid)
    res, data = postdata(client, "invenio_records_rest.item_list", new_acq2)
    assert res.status_code == 201

    # check item creation and indexation
    doc_list = url_for("invenio_records_rest.doc_list", view="global", q="pid:doc1")
    res = client.get(doc_list, headers=rero_json_header)
    data = get_json(res)
    assert len(data["hits"]["hits"]) == 1
    data = data["hits"]["hits"][0]["metadata"]
    assert len(data["holdings"]) == 2
    assert len(data["holdings"][0]["items"]) == 1
    assert len(data["holdings"][1]["items"]) == 1

    # check new_acquisition filters
    #   --> For org2, there is no new acquisition
    doc_list = url_for(
        "invenio_records_rest.doc_list",
        view="global",
        new_acquisition=":",
        organisation="org2",
    )
    res = client.get(doc_list, headers=rero_json_header)
    data = get_json(res)
    assert data["hits"]["total"] == 0

    #   --> for org1, there is 1 document with 2 new acquisition items
    doc_list = url_for(
        "invenio_records_rest.doc_list",
        view="global",
        new_acquisition=f"{past}:{future_1}",
        organisation="org1",
    )
    res = client.get(doc_list, headers=rero_json_header)
    data = get_json(res)
    assert data["hits"]["total"] == 1
    assert len(data["hits"]["hits"][0]["metadata"]["holdings"]) == 2

    #   --> for lib2, there is 1 document with 1 new acquisition items
    doc_list = url_for(
        "invenio_records_rest.doc_list",
        view="global",
        new_acquisition=f"{past}:{future_1}",
        library="lib2",
    )
    res = client.get(doc_list, headers=rero_json_header)
    data = get_json(res)
    assert data["hits"]["total"] == 1

    #   --> for loc3, there is 1 document with 1 new acquisition items
    doc_list = url_for(
        "invenio_records_rest.doc_list",
        view="global",
        new_acquisition=f"{past}:{future_1}",
        location="loc3",
    )
    res = client.get(doc_list, headers=rero_json_header)
    data = get_json(res)
    assert data["hits"]["total"] == 1

    #   --> for loc3, there is no document corresponding to range date
    doc_list = url_for(
        "invenio_records_rest.doc_list",
        view="global",
        new_acquisition=f"{past}:{today}",
        location="loc3",
    )
    res = client.get(doc_list, headers=rero_json_header)
    data = get_json(res)
    assert data["hits"]["total"] == 0

    #   --> for loc1 or loc3, there is 1 document with 2 new acquisition
    #       items (multiple `location` values are combined with OR)
    doc_list = url_for(
        "invenio_records_rest.doc_list",
        view="global",
        new_acquisition=f"{past}:{future_1}",
        location=["loc1", "loc3"],
    )
    res = client.get(doc_list, headers=rero_json_header)
    data = get_json(res)
    assert data["hits"]["total"] == 1
    assert len(data["hits"]["hits"][0]["metadata"]["holdings"]) == 2

    # check new_acquisition filters with -- separator and timestamp
    # Ex: 1696111200000--1700089200000
    doc_list = url_for(
        "invenio_records_rest.doc_list",
        view="global",
        acquisition=f"{acq_past_timestamp}--{acq_future_timestamp}",
    )
    res = client.get(doc_list, headers=rero_json_header)
    data = get_json(res)
    assert data["hits"]["total"] == 1

    # check that several `location` filter values are combined with OR
    # across DIFFERENT documents, not just within a single document.
    #   --> document_sion_items has a new acquisition in loc1 only ;
    #       export_document has a new acquisition in loc3 only.
    far_past = datetime_delta(days=-100).strftime("%Y-%m-%d")
    far_future = datetime_delta(days=100).strftime("%Y-%m-%d")

    new_acq_sion = deepcopy(item_lib_martigny_data)
    new_acq_sion["pid"] = "itemacqsion"
    new_acq_sion["document"]["$ref"] = get_ref_for_pid("doc", document_sion_items.pid)
    new_acq_sion["acquisition_date"] = today
    res, data = postdata(client, "invenio_records_rest.item_list", new_acq_sion)
    assert res.status_code == 201

    new_acq_export = deepcopy(item_lib_martigny_data)
    new_acq_export["pid"] = "itemacqexport"
    new_acq_export["document"]["$ref"] = get_ref_for_pid("doc", export_document.pid)
    new_acq_export["location"]["$ref"] = get_ref_for_pid("loc", loc_public_saxon.pid)
    new_acq_export["acquisition_date"] = today
    res, data = postdata(client, "invenio_records_rest.item_list", new_acq_export)
    assert res.status_code == 201

    #   --> for loc1 or loc3, both document_sion_items and export_document
    #       are returned, even though neither matches both locations on
    #       its own. This would fail without combining repeated
    #       `location` values with OR (see acquisition_filter in
    #       rero_ils/modules/documents/query.py)
    doc_list = url_for(
        "invenio_records_rest.doc_list",
        view="global",
        new_acquisition=f"{far_past}:{far_future}",
        location=["loc1", "loc3"],
        q="pid:doc3 OR pid:doc8",
    )
    res = client.get(doc_list, headers=rero_json_header)
    data = get_json(res)
    assert data["hits"]["total"] == 2

    # malformed timestamp range must return a clean 400 Bad Request
    doc_list = url_for(
        "invenio_records_rest.doc_list",
        view="global",
        new_acquisition="foo--bar",
    )
    res = client.get(doc_list, headers=rero_json_header)
    assert res.status_code == 400


@mock.patch(
    "invenio_records_rest.views.verify_record_permission",
    mock.MagicMock(return_value=VerifyRecordPermissionPatch),
)
def test_documents_facets(
    client,
    document_with_files,
    document2_ref,
    ebook_1,
    ebook_2,
    ebook_3,
    ebook_4,
    item_lib_martigny,
    rero_json_header,
):
    """Test record retrieval."""
    # STEP#1 :: CHECK FACETS ARE PRESENT INTO SEARCH RESULT
    url = url_for("invenio_records_rest.doc_list", view="global")
    res = client.get(url, headers=rero_json_header)
    data = get_json(res)
    facet_keys = [
        "document_type",
        "fiction_statement",
        "organisation",
        "language",
        "year",
        "author",
        "subject",
        "genreForm",
        "intendedAudience",
        "acquisition",
        "status",
    ]
    assert all(key in data["aggregations"] for key in facet_keys)

    params = {"view": "global", "facets": ""}
    url = url_for("invenio_records_rest.doc_list", **params)
    res = client.get(url, headers=rero_json_header)
    data = get_json(res)
    assert not data["aggregations"]

    params = {"view": "global", "facets": "document_type"}
    url = url_for("invenio_records_rest.doc_list", **params)
    res = client.get(url, headers=rero_json_header)
    data = get_json(res)
    assert list(data["aggregations"].keys()) == ["document_type"]

    params = {"view": "org1", "facets": "document_type"}
    url = url_for("invenio_records_rest.doc_list", **params)
    res = client.get(url, headers=rero_json_header)
    data = get_json(res)
    assert list(data["aggregations"].keys()) == ["document_type"]

    # test the patch that the library facet is computed by the serializer
    params = {"view": "org1", "facets": "document_type,library,author"}
    url = url_for("invenio_records_rest.doc_list", **params)
    res = client.get(url, headers=rero_json_header)
    data = get_json(res)
    aggs = data["aggregations"]
    assert set(aggs.keys()) == {"document_type", "library", "author"}

    # TEST FILTERS
    # Each filter checks is a tuple. First tuple element is argument used to
    # call the API, second tuple argument is the number of document that
    # should be return by the API call.
    checks = [
        ({"view": "global", "author": "Peter James"}, 2),
        ({"view": "global", "author": "Great Edition"}, 1),
        ({"view": "global", "author": "J.K. Rowling"}, 1),
        ({"view": "global", "author": ["Great Edition", "Peter James"]}, 1),
        ({"view": "global", "author": ["J.K. Rowling", "Peter James"]}, 0),
        # i18n facets
        ({"view": "global", "author": "Nebehay, Christian Michael"}, 1),
        (
            {
                "view": "global",
                "author": "Nebehay, Christian Michael, 1909-2003",
                "lang": "de",
            },
            0,
        ),
        ({"view": "global", "author": "Nebehay, Christian Michael", "lang": "thl"}, 1),
        ({"view": "global", "online": "true"}, 2),
        ({"view": "global", "organisation": "org1"}, 3),
    ]
    for params, value in checks:
        url = url_for("invenio_records_rest.doc_list", **params)
        res = client.get(url)
        data = get_json(res)
        assert data["hits"]["total"] == value


@pytest.fixture
def resource_document(app, document_data_tmp):
    """Create an isolated document for resource-filter tests."""
    document_data_tmp.pop("electronicLocator", None)
    document = Document.create(document_data_tmp, delete_pid=True, dbcommit=True, reindex=True)
    yield document
    for hit in ItemsSearch().filter("term", document__pid=document.pid).source("pid").scan():
        Item.get_record_by_pid(hit.pid).delete(force=True, dbcommit=True, delindex=True)
    for hit in HoldingsSearch().filter("term", document__pid=document.pid).source("pid").scan():
        Holding.get_record_by_pid(hit.pid).delete(force=True, dbcommit=True, delindex=True)
    document.delete(force=True, dbcommit=True, delindex=True)


@pytest.fixture
def physical_resource_item(
    resource_document, item_lib_martigny_data_tmp, item_type_standard_martigny, loc_public_martigny
):
    """Create a physical item on the isolated resource-filter document."""
    data = item_lib_martigny_data_tmp
    data["document"] = {"$ref": get_ref_for_pid("doc", resource_document.pid)}
    data["location"] = {"$ref": get_ref_for_pid("loc", loc_public_martigny.pid)}
    data["barcode"] = f"3594-{resource_document.pid}"
    return Item.create(data, delete_pid=True, dbcommit=True, reindex=True)


def _assert_resource_filters(client, document, online, physical):
    """Check the document PID returned by each switch combination."""
    for filters, included in [
        ({"online": "true"}, online),
        ({"not_online": "true"}, physical),
        ({"online": "true", "not_online": "true"}, online and physical),
    ]:
        url = url_for("invenio_records_rest.doc_list", view="global", q=f"pid:{document.pid}", **filters)
        response = client.get(url)
        assert response.status_code == 200
        pids = {hit["metadata"]["pid"] for hit in get_json(response)["hits"]["hits"]}
        assert pids == ({document.pid} if included else set())


@pytest.mark.parametrize(
    ("permanent_online", "temporary_online", "add_physical_item", "online", "physical"),
    [
        pytest.param(False, None, False, False, True, id="physical-only"),
        pytest.param(True, None, False, True, False, id="online-only"),
        pytest.param(False, True, False, True, False, id="temporary-online-only"),
        pytest.param(True, False, False, True, False, id="online-with-temporary-physical"),
        pytest.param(True, None, True, True, True, id="mixed-permanent-online"),
        pytest.param(False, True, True, True, True, id="mixed-temporary-online"),
    ],
)
def test_documents_item_resource_filters(
    client,
    resource_document,
    item_lib_martigny_data_tmp,
    item_type_standard_martigny,
    loc_public_martigny,
    loc_online_martigny,
    permanent_online,
    temporary_online,
    add_physical_item,
    online,
    physical,
):
    """Classify permanent, temporary and mixed item locations."""
    data = item_lib_martigny_data_tmp
    data["document"] = {"$ref": get_ref_for_pid("doc", resource_document.pid)}
    data["barcode"] = f"3594-{resource_document.pid}-1"
    location = loc_online_martigny if permanent_online else loc_public_martigny
    data["location"] = {"$ref": get_ref_for_pid("loc", location.pid)}
    if temporary_online is not None:
        temporary_location = loc_online_martigny if temporary_online else loc_public_martigny
        data["temporary_location"] = {"$ref": get_ref_for_pid("loc", temporary_location.pid)}
    Item.create(deepcopy(data), delete_pid=True, dbcommit=True, reindex=True)
    if add_physical_item:
        data.pop("temporary_location", None)
        data["location"] = {"$ref": get_ref_for_pid("loc", loc_public_martigny.pid)}
        data["barcode"] = f"3594-{resource_document.pid}-2"
        Item.create(data, delete_pid=True, dbcommit=True, reindex=True)

    _assert_resource_filters(client, resource_document, online, physical)
    indexed = DocumentsSearch().get_record_by_pid(resource_document.pid)
    assert indexed["has_online_item"] is online
    assert indexed["has_physical_resources"] is physical


@pytest.mark.parametrize("source", ["file", "resource", "versionOfResource", "electronic"])
@pytest.mark.parametrize("with_physical_item", [False, True], ids=["online-source-only", "with-physical-item"])
def test_documents_existing_online_resource_filters(
    client,
    resource_document,
    item_lib_martigny_data_tmp,
    item_type_standard_martigny,
    loc_public_martigny,
    lib_martigny,
    file_location,
    source,
    with_physical_item,
):
    """Keep files, qualifying links and electronic holdings online."""
    if source == "file":
        create_pdf_record_files(resource_document, {"library": {"$ref": get_ref_for_pid("lib", lib_martigny.pid)}})
    elif source == "electronic":
        data = _facet_holding_data(resource_document, loc_public_martigny, item_type_standard_martigny)
        data["holdings_type"] = "electronic"
        data["electronic_location"] = [{"uri": "https://example.org/3594"}]
        Holding.create(data, dbcommit=True, reindex=True)
    else:
        resource_document["electronicLocator"] = [{"type": source, "url": "https://example.org/3594"}]
        resource_document.update(resource_document, dbcommit=True, reindex=True)
    if with_physical_item:
        data = item_lib_martigny_data_tmp
        data["document"] = {"$ref": get_ref_for_pid("doc", resource_document.pid)}
        data["barcode"] = f"3594-{resource_document.pid}"
        Item.create(data, delete_pid=True, dbcommit=True, reindex=True)

    _assert_resource_filters(client, resource_document, online=True, physical=with_physical_item)


@pytest.mark.parametrize("removal", ["manual", "cleanup"])
def test_documents_temporary_online_location_removal(
    client, resource_document, physical_resource_item, loc_online_martigny, removal
):
    """Restore physical classification when the temporary online location is removed."""
    item = physical_resource_item
    item["temporary_location"] = {"$ref": get_ref_for_pid("loc", loc_online_martigny.pid)}
    if removal == "cleanup":
        item["temporary_location"]["end_date"] = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
    item.update(item, dbcommit=True, reindex=True)
    _assert_resource_filters(client, resource_document, online=True, physical=False)

    if removal == "cleanup":
        clean_obsolete_temporary_item_types_and_locations()
    else:
        item.pop("temporary_location")
        item.update(item, dbcommit=True, reindex=True)
    assert "temporary_location" not in Item.get_record(item.id)
    _assert_resource_filters(client, resource_document, online=False, physical=True)


def test_documents_resource_filters_after_item_deletion(client, resource_document, physical_resource_item):
    """Remove physical classification when the last item and its holding are deleted."""
    _assert_resource_filters(client, resource_document, online=False, physical=True)
    physical_resource_item.delete(force=True, dbcommit=True, delindex=True)
    _assert_resource_filters(client, resource_document, online=False, physical=False)


def test_documents_resource_filters_without_individual_item_reads(client, resource_document, physical_resource_item):
    """Classify resources without loading item records individually."""
    with (
        mock.patch.object(Item, "get_record_by_pid", side_effect=AssertionError("Individual item lookup")),
        mock.patch.object(Item, "get_records_by_pids", side_effect=AssertionError("Individual item lookups")),
    ):
        resource_document.reindex()
    _assert_resource_filters(client, resource_document, online=False, physical=True)


def test_documents_missing_item_location(client, resource_document, physical_resource_item):
    """Cache a missing location as non-online and finish indexing the document."""
    item = physical_resource_item
    item["temporary_location"] = deepcopy(item["location"])
    item.update(item, dbcommit=True, reindex=True)
    with mock.patch("rero_ils.modules.locations.api.Location.get_record_by_pid", return_value=None) as location_lookup:
        resource_document.reindex()
        location_lookup.assert_called_once_with(item.location_pid)
    _assert_resource_filters(client, resource_document, online=False, physical=True)


def test_documents_empty_holding_resource_filters(
    client, resource_document, loc_public_martigny, item_type_standard_martigny
):
    """Preserve physical classification of standard holdings without items."""
    _assert_resource_filters(client, resource_document, online=False, physical=False)
    Holding.create(
        _facet_holding_data(resource_document, loc_public_martigny, item_type_standard_martigny),
        dbcommit=True,
        reindex=True,
    )
    _assert_resource_filters(client, resource_document, online=False, physical=True)


def test_documents_deleted_item_resource_filters(
    client,
    resource_document,
    item_lib_martigny_data_tmp,
    item_type_standard_martigny,
    loc_online_martigny,
):
    """Ignore a deleted item whose search-index removal is still pending."""
    data = item_lib_martigny_data_tmp
    data["document"] = {"$ref": get_ref_for_pid("doc", resource_document.pid)}
    data["location"] = {"$ref": get_ref_for_pid("loc", loc_online_martigny.pid)}
    data["barcode"] = f"3594-deleted-{resource_document.pid}"
    item = Item.create(data, delete_pid=True, dbcommit=True, reindex=True)
    item.delete(force=True, dbcommit=True, delindex=False)
    try:
        resource_document.reindex()
        _assert_resource_filters(client, resource_document, online=False, physical=True)
    finally:
        ItemsIndexer().delete(item)


@mock.patch(
    "invenio_records_rest.views.verify_record_permission",
    mock.MagicMock(return_value=VerifyRecordPermissionPatch),
)
def test_documents_organisation_facets(client, document, item_lib_martigny, item_lib_saxon, rero_json_header):
    """Test record retrieval."""
    list_url = url_for("invenio_records_rest.doc_list", view="global")

    res = client.get(list_url, headers=rero_json_header)
    data = get_json(res)
    aggs = data["aggregations"]

    # the stale holdings-based terms metadata (`sum_other_doc_count`,
    # `doc_count_error_upper_bound`) is dropped: it no longer matches the
    # document counts exposed on the buckets.
    assert aggs["organisation"]["buckets"] == [
        {
            "doc_count": 3,
            "key": "org1",
            "library": {
                "buckets": [
                    {
                        "doc_count": 2,
                        "key": "lib1",
                        "location": {
                            "buckets": [{"doc_count": 2, "key": "loc1", "name": "Martigny Library Public Space"}],
                        },
                        "name": "Library of Martigny-ville",
                    },
                    {
                        "doc_count": 2,
                        "key": "lib2",
                        "location": {
                            "buckets": [{"doc_count": 2, "key": "loc3", "name": "Saxon Library Public Space"}],
                        },
                        "name": "Library of Saxon",
                    },
                ],
            },
            "name": "The district of Martigny Libraries",
        }
    ]

    # Test with filter for fiction_statement = unspecified
    list_url = url_for("invenio_records_rest.doc_list", view="global", fiction_statement="unspecified")

    res = client.get(list_url, headers=rero_json_header)
    data = get_json(res)
    aggs = data["aggregations"]

    assert aggs["organisation"]["buckets"] == [
        {
            "doc_count": 3,
            "key": "org1",
            "library": {
                "buckets": [
                    {
                        "doc_count": 2,
                        "key": "lib1",
                        "location": {
                            "buckets": [{"doc_count": 2, "key": "loc1", "name": "Martigny Library Public Space"}],
                        },
                        "name": "Library of Martigny-ville",
                    },
                    {
                        "doc_count": 2,
                        "key": "lib2",
                        "location": {
                            "buckets": [{"doc_count": 2, "key": "loc3", "name": "Saxon Library Public Space"}],
                        },
                        "name": "Library of Saxon",
                    },
                ],
            },
            "name": "The district of Martigny Libraries",
        }
    ]

    # Test with filter for fiction_statement = fiction
    list_url = url_for("invenio_records_rest.doc_list", view="global", fiction_statement="fiction")

    res = client.get(list_url, headers=rero_json_header)
    data = get_json(res)
    aggs = data["aggregations"]

    # no document matches `fiction`; every reverse_nested count is 0, so all
    # buckets are pruned. `min_doc_count=0` still makes Elasticsearch emit the
    # (empty) buckets, so the rewrite runs and drops the stale holdings-based
    # terms metadata even for an empty result set.
    assert aggs["organisation"]["buckets"] == []
    assert "sum_other_doc_count" not in aggs["organisation"]
    assert "doc_count_error_upper_bound" not in aggs["organisation"]


def _facet_holding_data(document, location, item_type):
    """Build minimal standard holding data (library/org come from location)."""
    return {
        "document": {"$ref": get_ref_for_pid("doc", document.pid)},
        "circulation_category": {"$ref": get_ref_for_pid("itty", item_type.pid)},
        "location": {"$ref": get_ref_for_pid("loc", location.pid)},
        "holdings_type": "standard",
    }


@mock.patch(
    "invenio_records_rest.views.verify_record_permission",
    mock.MagicMock(return_value=VerifyRecordPermissionPatch),
)
def test_documents_organisation_facet_document_count_order(
    client,
    app,
    rero_json_header,
    org_sion,
    lib_sion,
    lib_aproz,
    loc_public_sion,
    loc_restricted_sion,
    loc_online_sion,
    loc_online_aproz,
    item_type_internal_sion,
    document_data,
):
    """Test the `size` cut keeps the buckets with the most documents.

    The org/library/location facet runs on the `nested_holdings` nested field,
    so Elasticsearch orders the terms buckets by holdings count. When the
    number of buckets exceeds the aggregation `size`, a library (or location)
    with many documents but few holdings could be dropped before the serializer
    re-sorts. The terms aggregations must therefore order by `record_count`
    (the document count) in the query itself.
    """
    # Two libraries of the same organisation:
    #   * `lib_sion` gets 3 holdings, but all on a single document;
    #   * `lib_aproz` gets 2 holdings, on two distinct documents.
    # Elasticsearch orders terms by holdings count, so `lib_sion` (3 holdings)
    # comes before `lib_aproz` (2 holdings) even though `lib_aproz` has more
    # documents.
    documents = [
        Document.create(deepcopy(document_data), delete_pid=True, dbcommit=True, reindex=True) for _ in range(3)
    ]
    doc_a, doc_b, doc_c = documents

    holdings = [
        Holding.create(
            _facet_holding_data(doc_a, location, item_type_internal_sion), delete_pid=True, dbcommit=True, reindex=True
        )
        for location in (loc_public_sion, loc_restricted_sion, loc_online_sion)
    ]
    holdings += [
        Holding.create(
            _facet_holding_data(document, loc_online_aproz, item_type_internal_sion),
            delete_pid=True,
            dbcommit=True,
            reindex=True,
        )
        for document in (doc_b, doc_c)
    ]
    HoldingsSearch.flush_and_refresh()
    for document in documents:
        document.reindex()
    DocumentsSearch.flush_and_refresh()

    try:
        # Shrink the library `size` to 1: with two libraries, the size cut now
        # keeps a single bucket, reproducing the "buckets exceed the limit"
        # situation with a minimal dataset.
        facets = deepcopy(app.config["RECORDS_REST_FACETS"])
        library_agg = facets["documents"]["aggs"]["organisation"]["aggs"]["nested_holdings"]["aggs"]["organisation"][
            "aggs"
        ]["library"]
        library_agg["terms"]["size"] = 1
        with mock.patch.dict(app.config, {"RECORDS_REST_FACETS": facets}):
            list_url = url_for("invenio_records_rest.doc_list", view="org2")
            res = client.get(list_url, headers=rero_json_header)
        aggs = get_json(res)["aggregations"]

        # `lib_aproz` (2 documents) must survive the size cut; `lib_sion`
        # (3 holdings but 1 document) must be dropped. Ordering by holdings
        # count would keep `lib_sion` and lose `lib_aproz`.
        library_buckets = aggs["library"]["buckets"]
        assert [bucket["key"] for bucket in library_buckets] == [lib_aproz.pid]
        assert library_buckets[0]["doc_count"] == 2
        location_buckets = library_buckets[0]["location"]["buckets"]
        assert [bucket["key"] for bucket in location_buckets] == [loc_online_aproz.pid]
        assert location_buckets[0]["doc_count"] == 2
        # the stale holdings-based terms metadata is dropped: here the size cut
        # dropped `lib_sion`, so Elasticsearch reported a non-zero
        # `sum_other_doc_count` (its 3 holdings) that no longer makes sense.
        assert "sum_other_doc_count" not in aggs["library"]
        assert "doc_count_error_upper_bound" not in aggs["library"]
    finally:
        for holding in holdings:
            holding.delete(force=True, dbcommit=True, delindex=True)
        HoldingsSearch.flush_and_refresh()
        for document in documents:
            document.delete(force=True, dbcommit=True, delindex=True)
        DocumentsSearch.flush_and_refresh()


@mock.patch(
    "invenio_records_rest.views.verify_record_permission",
    mock.MagicMock(return_value=VerifyRecordPermissionPatch),
)
def test_documents_library_location_facets(client, document, org_martigny, item_lib_martigny, rero_json_header):
    """Test record retrieval."""
    list_url = url_for("invenio_records_rest.doc_list", view="org1")

    res = client.get(list_url, headers=rero_json_header)
    data = get_json(res)
    aggs = data["aggregations"]

    assert "library" in aggs

    # Test if location sub-buckets exists under each Library hit
    for hit in aggs["library"]["buckets"]:
        assert "location" in hit


@mock.patch(
    "invenio_records_rest.views.verify_record_permission",
    mock.MagicMock(return_value=VerifyRecordPermissionPatch),
)
def test_documents_post_put_delete(client, document_chinese_data, json_header, rero_json_header):
    """Test record retrieval."""
    # Create record / POST
    item_url = url_for("invenio_records_rest.doc_item", pid_value="4")

    document_chinese_data["pid"] = "4"
    res, data = postdata(client, "invenio_records_rest.doc_list", document_chinese_data)

    assert res.status_code == 201

    # Check that the returned record matches the given data
    test_data = data["metadata"]
    test_data.pop("sort_title", None)
    assert clean_text(test_data) == document_chinese_data

    res = client.get(item_url)
    assert res.status_code == 200
    data = get_json(res)

    test_data = data["metadata"]
    test_data.pop("sort_title", None)
    assert clean_text(test_data) == document_chinese_data
    expected_title = [
        {
            "_text": "\u56fd\u9645\u6cd5 : subtitle (Chinese). "
            "Part Number (Chinese), Part Name (Chinese) = "
            "International law (Chinese) : "
            "Parallel Subtitle (Chinese). "
            "Parallel Part Number (Chinese), "
            "Parallel Part Name (Chinese) = "
            "Parallel Title 2 (Chinese) : "
            "Parallel Subtitle 2 (Chinese)",
            "mainTitle": [
                {"value": "Guo ji fa"},
                {"value": "\u56fd\u9645\u6cd5", "language": "chi-hani"},
            ],
            "subtitle": [
                {"value": "subtitle (Latin)"},
                {"value": "subtitle (Chinese)", "language": "chi-hani"},
            ],
            "part": [
                {
                    "partNumber": [
                        {"value": "Part Number (Latin)"},
                        {"value": "Part Number (Chinese)", "language": "chi-hani"},
                    ],
                    "partName": [
                        {"value": "Part Name (Latin)"},
                        {"language": "chi-hani", "value": "Part Name (Chinese)"},
                    ],
                }
            ],
            "type": "bf:Title",
        },
        {
            "mainTitle": [
                {"value": "International law (Latin)"},
                {"value": "International law (Chinese)", "language": "chi-hani"},
            ],
            "subtitle": [
                {"value": "Parallel Subtitle (Latin)"},
                {"value": "Parallel Subtitle (Chinese)", "language": "chi-hani"},
            ],
            "part": [
                {
                    "partNumber": [
                        {"value": "Parallel Part Number (Latin)"},
                        {
                            "value": "Parallel Part Number (Chinese)",
                            "language": "chi-hani",
                        },
                    ],
                    "partName": [
                        {"value": "Parallel Part Name (Latin)"},
                        {
                            "language": "chi-hani",
                            "value": "Parallel Part Name (Chinese)",
                        },
                    ],
                }
            ],
            "type": "bf:ParallelTitle",
        },
        {
            "mainTitle": [
                {"value": "Parallel Title 2 (Latin)"},
                {"value": "Parallel Title 2 (Chinese)", "language": "chi-hani"},
            ],
            "subtitle": [
                {"value": "Parallel Subtitle 2 (Latin)"},
                {"value": "Parallel Subtitle 2 (Chinese)", "language": "chi-hani"},
            ],
            "type": "bf:ParallelTitle",
        },
        {"mainTitle": [{"value": "Guojifa"}], "type": "bf:VariantTitle"},
    ]

    # Update record/PUT
    data = document_chinese_data
    res = client.put(item_url, data=json.dumps(data), headers=rero_json_header)
    assert res.status_code == 200
    # assert res.headers['ETag'] != f'"{librarie.revision_id}"'

    # Check that the returned record matches the given data
    data = get_json(res)
    assert data["metadata"]["title"] == expected_title
    assert data["metadata"]["ui_title_variants"] == ["Guojifa"]
    assert data["metadata"]["ui_title_altgr"] == [
        (
            "Guo ji fa : subtitle (Latin). Part Number (Latin), Part Name (Latin)"
            " = International law (Latin) : Parallel Subtitle (Latin)."
            " Parallel Part Number (Latin), Parallel Part Name (Latin)"
            " = Parallel Title 2 (Latin) : Parallel Subtitle 2 (Latin)"
        )
    ]
    assert data["metadata"]["ui_responsibilities"] == [
        "梁西原著主编, 王献枢副主编",
        "Liang Xi yuan zhu zhu bian, Wang Xianshu fu zhu bian",
    ]

    res = client.get(item_url)
    assert res.status_code == 200

    # Delete record/DELETE
    res = client.delete(item_url)
    assert res.status_code == 204

    res = client.get(item_url)
    assert res.status_code == 410


def test_documents_get_resolve_rero_json(
    client,
    document_ref,
    entity_person_data,
    rero_json_header,
):
    """Test record get with resolve and mimetype rero+json."""
    api_url = url_for("invenio_records_rest.doc_item", pid_value="doc2", resolve="1")
    res = client.get(api_url, headers=rero_json_header)
    assert res.status_code == 200
    metadata = get_json(res).get("metadata", {})
    pid = metadata["contribution"][0]["entity"]["pid"]
    assert pid == entity_person_data["pid"]


@mock.patch("requests.Session.get")
def test_documents_resolve(
    mock_contributions_mef_get,
    client,
    mef_agents_url,
    loc_public_martigny,
    document_ref,
    entity_person_response_data,
):
    """Test document detailed view with items filter."""
    res = client.get(url_for("invenio_records_rest.doc_item", pid_value="doc2"))
    assert res.json["metadata"]["contribution"] == [
        {
            "entity": {
                "$ref": f"{mef_agents_url}/rero/A017671081",
                "pid": "ent_pers",
            },
            "role": ["aut"],
        }
    ]
    assert res.status_code == 200

    mock_contributions_mef_get.return_value = mock_response(json_data=entity_person_response_data)
    res = client.get(url_for("invenio_records_rest.doc_item", pid_value="doc2", resolve="1"))
    assert res.json["metadata"]["contribution"][0]["entity"]["authorized_access_point_fr"]
    assert res.status_code == 200


def test_document_exclude_draft_records(client, document):
    """Test document exclude draft record."""
    list_url = url_for("invenio_records_rest.doc_list", q="Lingliang")
    res = client.get(list_url)
    hits = get_json(res)["hits"]
    assert hits["total"] == 1
    data = hits["hits"][0]["metadata"]
    assert data["pid"] == document.get("pid")

    document["_draft"] = True
    document.update(document, dbcommit=True, reindex=True)

    list_url = url_for("invenio_records_rest.doc_list", q="Lingliang")
    res = client.get(list_url)
    hits = get_json(res)["hits"]
    assert hits["total"] == 0

    document["_draft"] = False
    document.update(document, dbcommit=True, reindex=True)

    list_url = url_for("invenio_records_rest.doc_list", q="Lingliang")
    res = client.get(list_url)
    hits = get_json(res)["hits"]
    assert hits["total"] == 1


def test_document_identifiers_search(client, document):
    """Test search on `identifiedBy` document."""

    def success(response_data):
        data = response_data["hits"]
        return data["total"] == 1 and data["hits"][0]["metadata"]["pid"] == document.pid

    def failure(response_data):
        return response_data["hits"]["total"] == 0

    # STEP#1 :: SEARCH FOR AN EXISTING IDENTIFIER
    #   Search for an existing encoded document identifier. The ISBN-13 is
    #   encoded into document data. Search on this specific value will return
    #   a record.
    params = {"identifiers": "(bf:Isbn)9782844267788"}
    url = url_for("invenio_records_rest.doc_list", **params)
    res = client.get(url)
    assert success(get_json(res))

    # STEP#2 :: SEARCH FOR AN ALTERNATIVE IDENTIFIER
    #   Search for the alternative of the encoded ISBN-13 value. During the
    #   document indexing process the corresponding ISBN-10 is appended to
    #   identifier list. A search on this value should return the same
    #   document. Additionally, search with hyphens to validate the specific
    #   identifier analyzer used for this field.
    params = {"identifiers": "(bf:Isbn)2-84426-778-5"}
    url = url_for("invenio_records_rest.doc_list", **params)
    res = client.get(url)
    assert success(get_json(res))

    # STEP#3 :: SEARCH WITH ONLY IDENTIFIER VALUE
    #   Search only about an identifier value without specified any identifier
    #   type.
    params = {"identifiers": "R008745599"}
    url = url_for("invenio_records_rest.doc_list", **params)
    res = client.get(url)
    assert success(get_json(res))

    # STEP#4 :: SEARCH ON UNKNOWN IDENTIFIERS
    for id_value in ["dummy_identifiers", "(bf:Issn)9782844267788"]:
        params = {"identifiers": id_value}
        url = url_for("invenio_records_rest.doc_list", **params)
        res = client.get(url)
        assert failure(get_json(res))

    # STEP#5 :: GROUPED SEARCH
    #   Use this filter in combination with other filter. In this test, the
    #   document isn't an harvested document, but it contains the correct
    #   specified identifier.
    params = {"identifiers": "(bf:Ean)9782844267788", "q": "harvested:true"}
    url = url_for("invenio_records_rest.doc_list", **params)
    res = client.get(url)
    assert failure(get_json(res))

    params["q"] = "harvested:false"
    url = url_for("invenio_records_rest.doc_list", **params)
    res = client.get(url)
    assert success(get_json(res))

    # STEP#6 :: SEARCH USING SHORTCUT search KEYS
    #   'isbn' and 'issn' keys are added to the search stored document. These key
    #   only contains the corresponding identifiers value ; but analyzer
    #   allows search using hyphens or not.
    url = url_for("invenio_records_rest.doc_list", q="isbn:2-84426-778-5")
    res = client.get(url)
    assert success(get_json(res))

    # STEP#7 :: WILDCARD SEARCH
    #    `identifiers` filter allow to search on a partial identifier string
    #    (only for the identifier value part).
    params = {"identifiers": "R0087455*"}
    url = url_for("invenio_records_rest.doc_list", **params)
    res = client.get(url)
    assert success(get_json(res))

    params = {"identifiers": "(bf:Local)*87455*"}
    url = url_for("invenio_records_rest.doc_list", **params)
    res = client.get(url)
    assert success(get_json(res))

    params = {"identifiers": "*dummy_search*"}
    url = url_for("invenio_records_rest.doc_list", **params)
    res = client.get(url)
    assert failure(get_json(res))

    # STEP#8 :: SEARCH WITH MULTIPLE IDENTIFIERS
    #    If we send multiple identifiers, an OR query will be used to search on
    #    each of them.
    params = {"identifiers": ["dummy", "other_id", "(bf:Ean)9782844267788"]}
    url = url_for("invenio_records_rest.doc_list", **params)
    res = client.get(url)
    assert success(get_json(res))

    # STEP#9 :: SEARCH ABOUT INVALID EAN IDENTIFIER
    #    Ensure than if an invalid EAN identifier exists into the document
    #    metadata, this identifier is searchable anyway.
    original_data = deepcopy(document)
    document["identifiedBy"].append({"type": IdentifierType.EAN, "value": "invalid_ean_identifier"})
    document.update(document, dbcommit=True, reindex=True)
    DocumentsSearch.flush_and_refresh()

    params = {"identifiers": ["(bf:Ean)invalid_ean_identifier"]}
    url = url_for("invenio_records_rest.doc_list", **params)
    res = client.get(url)
    assert success(get_json(res))

    # RESET THE DOCUMENT
    document.update(original_data, dbcommit=True, reindex=True)


def test_document_current_library_on_request_parameter(
    app,
    db,
    client,
    system_librarian_martigny,
    lib_martigny,
    lib_martigny_bourg,
    document,
    json_header,
):
    """Test for library assignment if the current_library parameter is present in the request."""
    login_user_via_session(client, system_librarian_martigny.user)

    # Assign library pid with current_librarian information
    document["copyrightDate"] = ["© 2023"]
    doc_url = url_for("invenio_records_rest.doc_item", pid_value=document.pid)
    res = client.put(doc_url, data=json.dumps(document), headers=json_header)
    assert res.status_code == 200
    OperationLogsSearch.flush_and_refresh()
    oplg = next(
        OperationLogsSearch()
        .filter("term", record__type="doc")
        .filter("term", record__value=document.pid)
        .params(preserve_order=True)
        .sort({"date": "desc"})
        .scan()
    )
    assert oplg.library.value == lib_martigny.pid
    db.session.rollback()

    # Assign library pid with current_library request parameter
    document["copyrightDate"] = ["© 1971"]
    doc_url = url_for(
        "invenio_records_rest.doc_item",
        pid_value=document.pid,
        current_library=lib_martigny_bourg.pid,
    )
    res = client.put(doc_url, data=json.dumps(document), headers=json_header)
    assert res.status_code == 200
    OperationLogsSearch.flush_and_refresh()
    oplg = next(
        OperationLogsSearch()
        .filter("term", record__type="doc")
        .filter("term", record__value=document.pid)
        .params(preserve_order=True)
        .sort({"date": "desc"})
        .scan()
    )
    assert oplg.library.value == lib_martigny_bourg.pid
    db.session.rollback()


def test_document_advanced_search_config(app, db, client, system_librarian_martigny, document):
    """Test for advanced search config."""

    def check_field_data(key, field_data, data):
        """Check content of the field data."""
        field_data = field_data.get(key, [])
        assert len(field_data) > 0
        assert data == field_data[0]

    config_url = url_for("api_documents.advanced_search_config")

    res = client.get(config_url)
    assert res.status_code == 401

    login_user_via_session(client, system_librarian_martigny.user)

    res = client.get(config_url)
    assert res.status_code == 200

    json = res.json
    assert "fieldsConfig" in json
    assert "fieldsData" in json

    fields_config_data = json.get("fieldsConfig")
    assert len(fields_config_data) > 0
    fields_config_by_value = {field["value"]: field for field in fields_config_data}
    assert fields_config_data[0] == {
        "field": None,
        "label": "Everywhere",
        "value": "everywhere",
        "options": {
            "search_type": [
                {"label": "contains", "value": "contains"},
                {"label": "phrase", "value": "phrase"},
            ]
        },
    }
    assert fields_config_by_value["title"] == {
        "field": "title.*",
        "label": "Title",
        "value": "title",
        "options": {
            "search_type": [
                {"label": "contains", "value": "contains"},
                {"label": "phrase", "value": "phrase"},
            ]
        },
    }

    # Country: Only Phrase on search type options.
    assert fields_config_by_value["country"] == {
        "field": "provisionActivity.place.country",
        "label": "Country",
        "value": "country",
        "options": {
            "search_type": [
                {"label": "phrase", "value": "phrase"},
            ]
        },
    }

    field_data = json.get("fieldsData")
    data_keys = [
        "canton",
        "country",
        "rdaCarrierType",
        "rdaContentType",
        "rdaMediaType",
    ]
    assert data_keys == list(field_data.keys())

    check_field_data("canton", field_data, {"label": "canton_ag", "value": "ag"})
    check_field_data("country", field_data, {"label": "country_aa", "value": "aa"})
    check_field_data("rdaCarrierType", field_data, {"label": "rdact:1002", "value": "rdact:1002"})
    check_field_data("rdaContentType", field_data, {"label": "rdaco:1002", "value": "rdaco:1002"})
    check_field_data("rdaMediaType", field_data, {"label": "rdamt:1001", "value": "rdamt:1001"})

    # Authentication must still be checked when the response is cached.
    with client.session_transaction() as session:
        session.clear()
    res = client.get(config_url)
    assert res.status_code == 401


@mock.patch(
    "invenio_records_rest.views.verify_record_permission",
    mock.MagicMock(return_value=VerifyRecordPermissionPatch),
)
def test_document_fulltext(app, client, document_with_files, document_with_issn):
    """Test document with fulltext."""
    list_url = url_for(
        "invenio_records_rest.doc_list",
        q=f'fulltext:"Document ({document_with_files.pid})"',
        fulltext="true",
    )
    res = client.get(list_url)
    hits = get_json(res)["hits"]
    assert hits["total"] == 1
    data = hits["hits"][0]["metadata"]
    assert data["pid"] == document_with_files.pid
    # the document index should contains files informations
    metadata_files = data["files"]
    # required fields
    for field in ["collections", "file_name", "rec_id"]:
        assert field in list(metadata_files[0].keys())
    # check the file names
    assert {res["file_name"] for res in metadata_files} == {"doc_doc1_1.pdf", "logo_rero_ils.png"}
    # text should not be on the es sources
    assert not [res["text"] for res in metadata_files if res.get("text")]

    list_url = url_for(
        "invenio_records_rest.doc_list",
        q=f'"Document ({document_with_files.pid})"',
        fulltext="true",
    )
    res = client.get(list_url)
    hits = get_json(res)["hits"]
    assert hits["total"] == 1
    data = hits["hits"][0]["metadata"]
    assert data["pid"] == document_with_files.pid

    list_url = url_for("invenio_records_rest.doc_list", q=f'"Document ({document_with_files.pid})"')
    res = client.get(list_url)
    hits = get_json(res)["hits"]
    assert hits["total"] == 0

    list_url = url_for(
        "invenio_records_rest.doc_list",
        q=f'"Document ({document_with_files.pid})"',
        fulltext=0,
    )
    res = client.get(list_url)
    hits = get_json(res)["hits"]
    assert hits["total"] == 0

    # fulltext is not included by default but it can be accessed if it is
    # explicit
    list_url = url_for(
        "invenio_records_rest.doc_list",
        q=f'fulltext:"Document ({document_with_files.pid})"',
        fulltext=0,
    )
    res = client.get(list_url)
    hits = get_json(res)["hits"]
    assert hits["total"] == 1
