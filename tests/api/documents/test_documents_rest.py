# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Tests REST API documents."""
import json
from copy import deepcopy
from datetime import datetime, timedelta

import mock
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import VerifyRecordPermissionPatch, clean_text, flush_index, \
    get_json, mock_response, postdata, to_relative_url

from rero_ils.modules.commons.identifiers import IdentifierType
from rero_ils.modules.documents.api import DocumentsSearch
from rero_ils.modules.documents.utils import get_remote_cover
from rero_ils.modules.documents.views import can_request, \
    record_library_pickup_locations
from rero_ils.modules.operation_logs.api import OperationLogsSearch
from rero_ils.modules.utils import get_ref_for_pid


@mock.patch(
    "invenio_records_rest.views.verify_record_permission",
    mock.MagicMock(return_value=VerifyRecordPermissionPatch),
)
def test_documents_get(client, document_with_files):
    """Test record retrieval."""
    document = document_with_files

    def clean_es_metadata(metadata):
        """Clean contribution from authorized_access_point_"""
        # Contributions, subject and genreForm are i18n indexed field, so it's
        # too complicated to compare it from original record. Just take the
        # data from original record ... not best, but not real alternatives.
        if contribution := document.get("contribution"):
            metadata["contribution"] = contribution
        if subjects := document.get("subjects"):
            metadata["subjects"] = subjects
        if genreForms := document.get("genreForm"):
            metadata["genreForm"] = genreForms

        # REMOVE DYNAMICALLY ADDED ES KEYS (see indexer.py:IndexerDumper)
        metadata.pop("sort_date_new", None)
        metadata.pop("sort_date_old", None)
        metadata.pop("sort_title", None)
        metadata.pop("isbn", None)
        metadata.pop("issn", None)
        metadata.pop("nested_identifiers", None)
        metadata.pop("identifiedBy", None)
        metadata.pop("files", None)
        return metadata

    item_url = url_for("invenio_records_rest.doc_item", pid_value="doc1")
    res = client.get(item_url)
    assert res.status_code == 200
    assert res.headers["ETag"] == f'"{document.revision_id}"'
    data = get_json(res)
    # DEV NOTES : Why removing `identifiedBy` key
    #   During the ES enrichment process, we complete the original identifiers
    #   with alternate identifiers. So comparing ES data identifiers, to
    #   original data identifiers doesn't make sense.
    document_data = document.dumps()
    document_data.pop("identifiedBy", None)
    assert document_data == clean_es_metadata(data["metadata"])

    # Check self links
    res = client.get(to_relative_url(data["links"]["self"]))
    assert res.status_code == 200
    res_content = get_json(res)
    res_content.get("metadata", {}).pop("identifiedBy", None)
    assert data == res_content
    document_data = document.dumps()
    document_data.pop("identifiedBy", None)
    assert document_data == clean_es_metadata(data["metadata"])

    list_url = url_for(
        "invenio_records_rest.doc_list", q=f"pid:{document.pid}")
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
    data_clean = clean_es_metadata(metadata)
    document = document.replace_refs().dumps()
    document.pop("identifiedBy", None)
    assert document == data_clean

    list_url = url_for("invenio_records_rest.doc_list", q="Vincent Berthe")
    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data["hits"]["total"]["value"] == 1


def test_documents_newacq_filters(
    app,
    client,
    system_librarian_martigny,
    rero_json_header,
    document,
    holding_lib_martigny,
    holding_lib_saxon,
    loc_public_saxon,
    item_lib_martigny_data,
):
    login_user_via_session(client, system_librarian_martigny.user)

    def datetime_delta(**args):
        """Apply delta on date time."""
        return datetime.now() + timedelta(**args)

    def datetime_milliseconds(date):
        """datetime get milliseconds."""
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
    doc_list = url_for(
        "invenio_records_rest.doc_list", view="global", pid="doc1")
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
    assert data["hits"]["total"]["value"] == 0

    #   --> for org1, there is 1 document with 2 new acquisition items
    doc_list = url_for(
        "invenio_records_rest.doc_list",
        view="global",
        new_acquisition=f"{past}:{future_1}",
        organisation="org1",
    )
    res = client.get(doc_list, headers=rero_json_header)
    data = get_json(res)
    assert data["hits"]["total"]["value"] == 1
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
    assert data["hits"]["total"]["value"] == 1

    #   --> for loc3, there is 1 document with 1 new acquisition items
    doc_list = url_for(
        "invenio_records_rest.doc_list",
        view="global",
        new_acquisition=f"{past}:{future_1}",
        location="loc3",
    )
    res = client.get(doc_list, headers=rero_json_header)
    data = get_json(res)
    assert data["hits"]["total"]["value"] == 1

    #   --> for loc3, there is no document corresponding to range date
    doc_list = url_for(
        "invenio_records_rest.doc_list",
        view="global",
        new_acquisition=f"{past}:{today}",
        location="loc3",
    )
    res = client.get(doc_list, headers=rero_json_header)
    data = get_json(res)
    assert data["hits"]["total"]["value"] == 0

    # check new_acquisition filters with -- separator and timestamp
    # Ex: 1696111200000--1700089200000
    doc_list = url_for(
        "invenio_records_rest.doc_list",
        view="global",
        acquisition=f"{acq_past_timestamp}--{acq_future_timestamp}",
    )
    res = client.get(doc_list, headers=rero_json_header)
    data = get_json(res)
    assert data["hits"]["total"]["value"] == 1


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
        "author",
        "language",
        "subject",
        "fiction_statement",
        "genreForm",
        "intendedAudience",
        "year",
        "status",
        "acquisition"
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
        ({
            "view": "global",
            "author": "Nebehay, Christian Michael", "lang": "thl"}, 1),
        ({"view": "global", "online": "true"}, 1),
    ]
    for params, value in checks:
        url = url_for("invenio_records_rest.doc_list", **params)
        res = client.get(url)
        data = get_json(res)
        assert data["hits"]["total"]["value"] == value


@mock.patch(
    "invenio_records_rest.views.verify_record_permission",
    mock.MagicMock(return_value=VerifyRecordPermissionPatch),
)
def test_documents_organisation_facets(
    client, document, item_lib_martigny, rero_json_header
):
    """Test record retrieval."""
    list_url = url_for("invenio_records_rest.doc_list", view="global")

    res = client.get(list_url, headers=rero_json_header)
    data = get_json(res)
    aggs = data["aggregations"]

    assert "organisation" in aggs


@mock.patch(
    "invenio_records_rest.views.verify_record_permission",
    mock.MagicMock(return_value=VerifyRecordPermissionPatch),
)
def test_documents_library_location_facets(
    client, document, org_martigny, item_lib_martigny, rero_json_header
):
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
def test_documents_post_put_delete(
    client, document_chinese_data, json_header, rero_json_header
):
    """Test record retrieval."""
    # Create record / POST
    item_url = url_for("invenio_records_rest.doc_item", pid_value="4")
    list_url = url_for("invenio_records_rest.doc_list", q="pid:4")

    document_chinese_data["pid"] = "4"
    res, data = postdata(
        client, "invenio_records_rest.doc_list", document_chinese_data)

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
                        {
                            "value": "Part Number (Chinese)",
                            "language": "chi-hani"},
                    ],
                    "partName": [
                        {"value": "Part Name (Latin)"},
                        {
                            "language": "chi-hani",
                            "value": "Part Name (Chinese)"},
                    ],
                }
            ],
            "type": "bf:Title",
        },
        {
            "mainTitle": [
                {"value": "International law (Latin)"},
                {
                    "value": "International law (Chinese)",
                    "language": "chi-hani"},
            ],
            "subtitle": [
                {"value": "Parallel Subtitle (Latin)"},
                {
                    "value": "Parallel Subtitle (Chinese)",
                    "language": "chi-hani"},
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
                {
                    "value": "Parallel Title 2 (Chinese)",
                    "language": "chi-hani"},
            ],
            "subtitle": [
                {"value": "Parallel Subtitle 2 (Latin)"},
                {
                    "value": "Parallel Subtitle 2 (Chinese)",
                    "language": "chi-hani"},
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
        "Guo ji fa : subtitle (Latin). Part Number (Latin), Part Name (Latin)"
        " = International law (Latin) : Parallel Subtitle (Latin)."
        " Parallel Part Number (Latin), Parallel Part Name (Latin)"
        " = Parallel Title 2 (Latin) : Parallel Subtitle 2 (Latin)"
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
    api_url = url_for(
        "invenio_records_rest.doc_item", pid_value="doc2", resolve="1")
    res = client.get(api_url, headers=rero_json_header)
    assert res.status_code == 200
    metadata = get_json(res).get("metadata", {})
    pid = metadata["contribution"][0]["entity"]["pid"]
    assert pid == entity_person_data["pid"]


def test_document_can_request_view(
    client,
    item_lib_fully,
    loan_pending_martigny,
    document,
    patron_martigny,
    patron2_martigny,
    item_type_standard_martigny,
    circulation_policies,
    librarian_martigny,
    item_lib_martigny,
    item_lib_saxon,
    item_lib_sion,
    loc_public_martigny,
):
    """Test can request on document view."""
    login_user_via_session(client, patron_martigny.user)

    with mock.patch(
        "rero_ils.modules.documents.views.current_user", patron_martigny.user
    ), mock.patch(
        "rero_ils.modules.documents.views.current_patrons", [patron_martigny]
    ):
        can, _ = can_request(item_lib_fully)
        assert can
        can, _ = can_request(item_lib_sion)
        assert not can

    with mock.patch(
        "rero_ils.modules.documents.views.current_user", patron2_martigny.user
    ), mock.patch(
        "rero_ils.modules.documents.views.current_patrons", [patron2_martigny]
    ):
        can, _ = can_request(item_lib_fully)
        assert not can

    picks = record_library_pickup_locations(item_lib_fully)
    assert len(picks) == 3

    picks = record_library_pickup_locations(item_lib_martigny)
    assert len(picks) == 3


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
    res = client.get(
        url_for("invenio_records_rest.doc_item", pid_value="doc2"))
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

    mock_contributions_mef_get.return_value = mock_response(
        json_data=entity_person_response_data
    )
    res = client.get(
        url_for("invenio_records_rest.doc_item", pid_value="doc2", resolve="1")
    )
    assert res.json["metadata"]["contribution"][0]["entity"][
        "authorized_access_point_fr"
    ]
    assert res.status_code == 200


def test_document_exclude_draft_records(client, document):
    """Test document exclude draft record."""
    list_url = url_for("invenio_records_rest.doc_list", q="Lingliang")
    res = client.get(list_url)
    hits = get_json(res)["hits"]
    assert hits["total"]["value"] == 1
    data = hits["hits"][0]["metadata"]
    assert data["pid"] == document.get("pid")

    document["_draft"] = True
    document.update(document, dbcommit=True, reindex=True)

    list_url = url_for("invenio_records_rest.doc_list", q="Lingliang")
    res = client.get(list_url)
    hits = get_json(res)["hits"]
    assert hits["total"]["value"] == 0

    document["_draft"] = False
    document.update(document, dbcommit=True, reindex=True)

    list_url = url_for("invenio_records_rest.doc_list", q="Lingliang")
    res = client.get(list_url)
    hits = get_json(res)["hits"]
    assert hits["total"]["value"] == 1


@mock.patch("requests.get")
def test_get_remote_cover(mock_get_cover, app):
    """Test get remote cover."""
    mock_get_cover.return_value = mock_response(status=400)
    assert get_remote_cover("YYYYYYYYY") is None

    mock_get_cover.return_value = mock_response(
        content="thumb({"
        '    "success": true,'
        '    "image": "https://i.test.com/images/P/XXXXXXXXXX_.jpg"'
        "})"
    )
    cover = get_remote_cover("XXXXXXXXXX")
    assert cover == {
        "success": True,
        "image": "https://i.test.com/images/P/XXXXXXXXXX_.jpg",
    }


def test_document_identifiers_search(client, document):
    """Test search on `identifiedBy` document."""

    def success(response_data):
        data = response_data["hits"]
        return (
            data["total"]["value"] == 1
            and data["hits"][0]["metadata"]["pid"] == document.pid
        )

    def failure(response_data):
        return response_data["hits"]["total"]["value"] == 0

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

    # STEP#6 :: SEARCH USING SHORTCUT ES KEYS
    #   'isbn' and 'issn' keys are added to the ES stored document. These key
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
    document["identifiedBy"].append(
        {"type": IdentifierType.EAN, "value": "invalid_ean_identifier"}
    )
    document.update(document, dbcommit=True, reindex=True)
    flush_index(DocumentsSearch.Meta.index)

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
    """Test for library assignment if the current_library parameter
    is present in the request."""
    login_user_via_session(client, system_librarian_martigny.user)

    # Assign library pid with current_librarian information
    document["copyrightDate"] = ["© 2023"]
    doc_url = url_for("invenio_records_rest.doc_item", pid_value=document.pid)
    res = client.put(doc_url, data=json.dumps(document), headers=json_header)
    assert res.status_code == 200
    flush_index(OperationLogsSearch.Meta.index)
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
    flush_index(OperationLogsSearch.Meta.index)
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


def test_document_advanced_search_config(
    app, db, client, system_librarian_martigny, document
):
    """Test for advanced search config."""

    def check_field_data(key, field_data, data):
        """Check content of the field data."""
        field_data = field_data.get(key, [])
        assert 0 < len(field_data)
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
    assert 0 < len(fields_config_data)
    assert {
        "field": "title.*",
        "label": "Title",
        "value": "title",
        "options": {
            "search_type": [
                {"label": "contains", "value": "contains"},
                {"label": "phrase", "value": "phrase"},
            ]
        },
    } == fields_config_data[0]

    # Country: Only Phrase on search type options.
    assert {
        "field": "provisionActivity.place.country",
        "label": "Country",
        "value": "country",
        "options": {
            "search_type": [
                {"label": "phrase", "value": "phrase"},
            ]
        },
    } == fields_config_data[3]

    field_data = json.get("fieldsData")
    data_keys = [
        "canton",
        "country",
        "rdaCarrierType",
        "rdaContentType",
        "rdaMediaType",
    ]
    assert data_keys == list(field_data.keys())

    check_field_data(
        "canton", field_data, {"label": "canton_ag", "value": "ag"})
    check_field_data(
        "country", field_data, {"label": "country_aa", "value": "aa"})
    check_field_data(
        "rdaCarrierType", field_data,
        {"label": "rdact:1002", "value": "rdact:1002"}
    )
    check_field_data(
        "rdaContentType", field_data,
        {"label": "rdaco:1002", "value": "rdaco:1002"}
    )
    check_field_data(
        "rdaMediaType", field_data,
        {"label": "rdamt:1001", "value": "rdamt:1001"}
    )


@mock.patch(
    "invenio_records_rest.views.verify_record_permission",
    mock.MagicMock(return_value=VerifyRecordPermissionPatch),
)
def test_document_fulltext(client, document_with_files, document_with_issn):
    """Test document with fulltext."""
    list_url = url_for(
        "invenio_records_rest.doc_list",
        q=f'fulltext:"Document ({document_with_files.pid})"',
        fulltext="true",
    )
    res = client.get(list_url)
    hits = get_json(res)["hits"]
    assert hits["total"]["value"] == 1
    data = hits["hits"][0]["metadata"]
    assert data["pid"] == document_with_files.pid
    # the document index should contains files informations
    metadata_files = data["files"]
    # required fields
    for field in ["collections", "file_name", "rec_id"]:
        assert field in list(metadata_files[0].keys())
    # check the file names
    assert {res["file_name"] for res in metadata_files} == set(
        ("doc_doc1_1.pdf", "logo_rero_ils.png")
    )
    # text should not be on the es sources
    assert not [res["text"] for res in metadata_files if res.get("text")]

    list_url = url_for(
        "invenio_records_rest.doc_list",
        q=f'"Document ({document_with_files.pid})"',
        fulltext="true",
    )
    res = client.get(list_url)
    hits = get_json(res)["hits"]
    assert hits["total"]["value"] == 1
    data = hits["hits"][0]["metadata"]
    assert data["pid"] == document_with_files.pid

    list_url = url_for(
        "invenio_records_rest.doc_list",
        q=f'"Document ({document_with_files.pid})"'
    )
    res = client.get(list_url)
    hits = get_json(res)["hits"]
    assert hits["total"]["value"] == 0

    list_url = url_for(
        "invenio_records_rest.doc_list",
        q=f'"Document ({document_with_files.pid})"',
        fulltext=0,
    )
    res = client.get(list_url)
    hits = get_json(res)["hits"]
    assert hits["total"]["value"] == 0

    # fulltext is not included by default but it can be accessed if it is
    # explicit
    list_url = url_for(
        "invenio_records_rest.doc_list",
        q=f'fulltext:"Document ({document_with_files.pid})"',
        fulltext=0,
    )
    res = client.get(list_url)
    hits = get_json(res)["hits"]
    assert hits["total"]["value"] == 1
