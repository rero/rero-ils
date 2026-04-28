# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
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

from flask import url_for

from tests.utils import get_xml_dict


def test_sru_explain(client):
    """Test sru documents rest api."""
    api_url = url_for("api_sru.documents")
    res = client.get(api_url)
    assert res.status_code == 200
    xml_dict = get_xml_dict(res)
    assert "sru:explainResponse" in xml_dict


def test_sru_documents(client, document_ref, entity_person_data):
    """Test sru documents rest api."""
    api_url = url_for("api_sru.documents", version="1.1", operation="searchRetrieve", query="al-Wajīz")
    res = client.get(api_url)
    assert res.status_code == 200
    xml_dict = get_xml_dict(res)
    assert "zs:searchRetrieveResponse" in xml_dict
    search_rr = xml_dict["zs:searchRetrieveResponse"]
    assert search_rr.get("zs:echoedSearchRetrieveRequest") == {
        "zs:version": "1.1",
        "zs:maximumRecords": "100",
        "zs:query": "al-Wajīz",
        "zs:search_query": "al-Wajīz",
        "zs:recordPacking": "XML",
        "zs:recordSchema": "info:sru/schema/1/marcxml-v1.1-light",
        "zs:resultSetTTL": "0",
        "zs:startRecord": "1",
    }
    # Search should return only documents matching the query, not all documents
    assert search_rr.get("zs:numberOfRecords") == "1"


def test_sru_documents_items(client, document_sion_items):
    """Test sru documents with items."""
    api_url = url_for(
        "api_sru.documents",
        version="1.1",
        operation="searchRetrieve",
        query='"La reine Berthe et son fils"',
    )
    res = client.get(api_url)
    assert res.status_code == 200
    xml_dict = get_xml_dict(res)
    assert "zs:searchRetrieveResponse" in xml_dict
    ech_srr = xml_dict["zs:searchRetrieveResponse"]["zs:echoedSearchRetrieveRequest"]
    assert ech_srr["zs:query"] == '"La reine Berthe et son fils"'
    assert ech_srr["zs:search_query"] == '"La reine Berthe et son fils"'

    api_url = url_for(
        "api_sru.documents",
        version="1.1",
        operation="searchRetrieve",
        query='"La reine Berthe et son fils"',
        format="marcxml",
    )
    res = client.get(api_url)
    assert res.status_code == 200
    xml_dict = get_xml_dict(res)
    assert "zs:searchRetrieveResponse" in xml_dict
    ech_srr = xml_dict["zs:searchRetrieveResponse"]["zs:echoedSearchRetrieveRequest"]
    assert ech_srr["zs:query"] == '"La reine Berthe et son fils"'
    assert ech_srr["zs:search_query"] == '"La reine Berthe et son fils"'

    api_url = url_for(
        "api_sru.documents",
        version="1.1",
        operation="searchRetrieve",
        query='dc.title="La reine Berthe et son fils"',
        format="dc",
    )
    res = client.get(api_url)
    assert res.status_code == 200
    xml_dict = get_xml_dict(res)
    assert "searchRetrieveResponse" in xml_dict
    ech_srr = xml_dict["searchRetrieveResponse"]["echoedSearchRetrieveRequest"]
    assert ech_srr["query"] == 'dc.title="La reine Berthe et son fils"'
    assert ech_srr["search_query"] == 'title.\\*:"La reine Berthe et son fils"'


def test_sru_excludes_masked_and_draft(client, document_ref):
    """Test that SRU excludes masked and draft documents from results."""
    from rero_ils.modules.documents.api import DocumentsSearch

    api_url = url_for("api_sru.documents", version="1.1", operation="searchRetrieve", query="al-Wajīz")

    # Baseline: document is visible
    xml_dict = get_xml_dict(client.get(api_url))
    assert xml_dict["zs:searchRetrieveResponse"].get("zs:numberOfRecords") == "1"

    # Masked documents are hidden
    document_ref["_masked"] = True
    document_ref.update(document_ref, dbcommit=True, reindex=True)
    DocumentsSearch.flush_and_refresh()
    xml_dict = get_xml_dict(client.get(api_url))
    assert xml_dict["zs:searchRetrieveResponse"].get("zs:numberOfRecords") == "0"

    # Unmasking restores visibility
    document_ref["_masked"] = False
    document_ref.update(document_ref, dbcommit=True, reindex=True)
    DocumentsSearch.flush_and_refresh()
    xml_dict = get_xml_dict(client.get(api_url))
    assert xml_dict["zs:searchRetrieveResponse"].get("zs:numberOfRecords") == "1"

    # Draft documents are hidden
    document_ref["_draft"] = True
    document_ref.update(document_ref, dbcommit=True, reindex=True)
    DocumentsSearch.flush_and_refresh()
    xml_dict = get_xml_dict(client.get(api_url))
    assert xml_dict["zs:searchRetrieveResponse"].get("zs:numberOfRecords") == "0"

    # Restore state for other tests (fixture is module-scoped)
    document_ref["_draft"] = False
    document_ref.update(document_ref, dbcommit=True, reindex=True)
    DocumentsSearch.flush_and_refresh()


def test_sru_documents_diagnostics(client):
    """Test sru documents diagnostics."""
    api_url = url_for("api_sru.documents", version="1.1", operation="searchRetrieve", query="(((")
    res = client.get(api_url)
    assert res.status_code == 200
    xml_dict = get_xml_dict(res)
    assert "srw:searchRetrieveResponse" in xml_dict
    assert xml_dict["srw:searchRetrieveResponse"]["diag:diagnostics"]["diag:message"] == "Malformed Query"


def test_sru_explain_conditional_get(client):
    """Test SRU explain returns 304 Not Modified when ETag matches."""
    api_url = url_for("api_sru.documents")
    res = client.get(api_url)
    assert res.status_code == 200
    etag = res.headers.get("ETag")
    assert etag
    # Conditional GET with matching ETag should return 304
    res = client.get(api_url, headers={"If-None-Match": etag})
    assert res.status_code == 304
    assert res.headers.get("ETag") == etag


def test_sru_search_backend_error(client):
    """Test SRU returns a diagnostic on non-recoverable search backend error."""
    from unittest.mock import patch

    from elasticsearch.exceptions import RequestError as ESRequestError

    from rero_ils.modules.documents.api import DocumentsSearch

    api_url = url_for("api_sru.documents", version="1.1", operation="searchRetrieve", query="test")
    err = ESRequestError(500, "internal_error", "cluster is unavailable")
    with patch.object(DocumentsSearch, "execute", side_effect=err):
        res = client.get(api_url)
    assert res.status_code == 200
    xml_dict = get_xml_dict(res)
    assert "srw:searchRetrieveResponse" in xml_dict
    diag = xml_dict["srw:searchRetrieveResponse"]["diag:diagnostics"]
    assert diag["diag:message"] == "System temporarily unavailable"


def test_sru_search_window_overflow(client):
    """Test SRU returns zero results when search result window is exceeded."""
    from unittest.mock import patch

    from elasticsearch.exceptions import RequestError as ESRequestError

    from rero_ils.modules.documents.api import DocumentsSearch

    api_url = url_for(
        "api_sru.documents",
        version="1.1",
        operation="searchRetrieve",
        query="test",
        startRecord="100000",
    )
    err = ESRequestError(400, "search_phase_execution_exception", "Result window is too large")
    with patch.object(DocumentsSearch, "execute", side_effect=err):
        res = client.get(api_url)
    assert res.status_code == 200
    xml_dict = get_xml_dict(res)
    assert "zs:searchRetrieveResponse" in xml_dict
    assert xml_dict["zs:searchRetrieveResponse"]["zs:numberOfRecords"] == "0"


def test_sru_sort(client, document_sion_items):
    """Test SRU search with sortBy CQL clause."""
    api_url = url_for(
        "api_sru.documents",
        version="1.1",
        operation="searchRetrieve",
        query='"La reine Berthe et son fils" sortBy dc.title/ascending',
    )
    res = client.get(api_url)
    assert res.status_code == 200
    xml_dict = get_xml_dict(res)
    assert "zs:searchRetrieveResponse" in xml_dict
