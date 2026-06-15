# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests REST API documents."""

from flask import url_for

from rero_ils.modules.sru.cql_parser import SRU_MARCXML_SCHEMA_URI
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
        "zs:operation": "searchRetrieve",
        "zs:maximumRecords": "100",
        "zs:query": "al-Wajīz",
        "zs:search_query": "al-Wajīz",
        "zs:recordPacking": "XML",
        "zs:recordSchema": SRU_MARCXML_SCHEMA_URI,
        "zs:resultSetTTL": "300",
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
        format="marcxmlsru",
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
    assert "zs:searchRetrieveResponse" in xml_dict
    ech_srr = xml_dict["zs:searchRetrieveResponse"]["zs:echoedSearchRetrieveRequest"]
    assert ech_srr["zs:query"] == 'dc.title="La reine Berthe et son fils"'
    assert ech_srr["zs:search_query"] == 'title.\\*:"La reine Berthe et son fils"'


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
    diag = xml_dict["srw:searchRetrieveResponse"]["srw:diagnostics"]["diag:diagnostic"]
    assert diag["diag:message"] == "Malformed Query"


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
    diag = xml_dict["srw:searchRetrieveResponse"]["srw:diagnostics"]["diag:diagnostic"]
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


def test_sru_unsupported_operation(client):
    """Test SRU returns diagnostic code 4 for an unknown operation."""
    api_url = url_for("api_sru.documents", operation="unknownOp")
    res = client.get(api_url)
    assert res.status_code == 200
    xml_dict = get_xml_dict(res)
    assert "srw:searchRetrieveResponse" in xml_dict
    diag = xml_dict["srw:searchRetrieveResponse"]["srw:diagnostics"]["diag:diagnostic"]
    assert diag["diag:uri"] == "info:srw/diagnostic/1/4"
    assert diag["diag:message"] == "Unsupported operation"
    assert diag["diag:details"] == "unknownOp"


def test_sru_invalid_start_record(client):
    """Test SRU returns diagnostic code 6 when startRecord is not an integer."""
    api_url = url_for("api_sru.documents", version="1.1", operation="searchRetrieve", query="test", startRecord="abc")
    res = client.get(api_url)
    assert res.status_code == 200
    xml_dict = get_xml_dict(res)
    assert "srw:searchRetrieveResponse" in xml_dict
    diag = xml_dict["srw:searchRetrieveResponse"]["srw:diagnostics"]["diag:diagnostic"]
    assert diag["diag:uri"] == "info:srw/diagnostic/1/6"
    assert diag["diag:message"] == "Unsupported parameter value"
    assert "startRecord" in diag["diag:details"]


def test_sru_invalid_maximum_records(client):
    """Test SRU returns diagnostic code 6 when maximumRecords is not an integer."""
    api_url = url_for(
        "api_sru.documents", version="1.1", operation="searchRetrieve", query="test", maximumRecords="xyz"
    )
    res = client.get(api_url)
    assert res.status_code == 200
    xml_dict = get_xml_dict(res)
    assert "srw:searchRetrieveResponse" in xml_dict
    diag = xml_dict["srw:searchRetrieveResponse"]["srw:diagnostics"]["diag:diagnostic"]
    assert diag["diag:uri"] == "info:srw/diagnostic/1/6"
    assert diag["diag:message"] == "Unsupported parameter value"
    assert "maximumRecords" in diag["diag:details"]


def test_sru_missing_query(client):
    """Test SRU returns diagnostic code 7 when searchRetrieve is called without a query."""
    api_url = url_for("api_sru.documents", version="1.1", operation="searchRetrieve")
    res = client.get(api_url)
    assert res.status_code == 200
    xml_dict = get_xml_dict(res)
    assert "srw:searchRetrieveResponse" in xml_dict
    diag = xml_dict["srw:searchRetrieveResponse"]["srw:diagnostics"]["diag:diagnostic"]
    assert diag["diag:uri"] == "info:srw/diagnostic/1/7"
    assert diag["diag:message"] == "Mandatory parameter not supplied"
    assert diag["diag:details"] == "query"


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


def test_sru_unsupported_version(client):
    """Test SRU returns diagnostic code 5 for an unsupported version."""
    api_url = url_for("api_sru.documents", version="2.0", operation="searchRetrieve", query="test")
    res = client.get(api_url)
    assert res.status_code == 200
    xml_dict = get_xml_dict(res)
    assert "srw:searchRetrieveResponse" in xml_dict
    diag = xml_dict["srw:searchRetrieveResponse"]["srw:diagnostics"]["diag:diagnostic"]
    assert diag["diag:uri"] == "info:srw/diagnostic/1/5"
    assert diag["diag:message"] == "Unsupported version"
    assert diag["diag:details"] == "2.0"


def test_sru_unsupported_record_packing(client):
    """Test SRU returns diagnostic code 6 for an unsupported recordPacking value."""
    api_url = url_for(
        "api_sru.documents",
        version="1.1",
        operation="searchRetrieve",
        query="test",
        recordPacking="json",
    )
    res = client.get(api_url)
    assert res.status_code == 200
    xml_dict = get_xml_dict(res)
    assert "srw:searchRetrieveResponse" in xml_dict
    diag = xml_dict["srw:searchRetrieveResponse"]["srw:diagnostics"]["diag:diagnostic"]
    assert diag["diag:uri"] == "info:srw/diagnostic/1/6"
    assert diag["diag:message"] == "Unsupported parameter value"
    assert "recordPacking" in diag["diag:details"]


def test_sru_start_record_zero(client):
    """Test SRU returns diagnostic code 6 when startRecord is 0 (must be >= 1)."""
    api_url = url_for("api_sru.documents", version="1.1", operation="searchRetrieve", query="test", startRecord="0")
    res = client.get(api_url)
    assert res.status_code == 200
    xml_dict = get_xml_dict(res)
    assert "srw:searchRetrieveResponse" in xml_dict
    diag = xml_dict["srw:searchRetrieveResponse"]["srw:diagnostics"]["diag:diagnostic"]
    assert diag["diag:uri"] == "info:srw/diagnostic/1/6"
    assert diag["diag:message"] == "Unsupported parameter value"
    assert "startRecord" in diag["diag:details"]


def test_sru_start_record_negative(client):
    """Test SRU returns diagnostic code 6 when startRecord is negative."""
    api_url = url_for("api_sru.documents", version="1.1", operation="searchRetrieve", query="test", startRecord="-1")
    res = client.get(api_url)
    assert res.status_code == 200
    xml_dict = get_xml_dict(res)
    assert "srw:searchRetrieveResponse" in xml_dict
    diag = xml_dict["srw:searchRetrieveResponse"]["srw:diagnostics"]["diag:diagnostic"]
    assert diag["diag:uri"] == "info:srw/diagnostic/1/6"
    assert diag["diag:message"] == "Unsupported parameter value"
    assert "startRecord" in diag["diag:details"]


def test_sru_maximum_records_negative(client):
    """Test SRU returns diagnostic code 6 when maximumRecords is negative."""
    api_url = url_for("api_sru.documents", version="1.1", operation="searchRetrieve", query="test", maximumRecords="-1")
    res = client.get(api_url)
    assert res.status_code == 200
    xml_dict = get_xml_dict(res)
    assert "srw:searchRetrieveResponse" in xml_dict
    diag = xml_dict["srw:searchRetrieveResponse"]["srw:diagnostics"]["diag:diagnostic"]
    assert diag["diag:uri"] == "info:srw/diagnostic/1/6"
    assert diag["diag:message"] == "Unsupported parameter value"
    assert "maximumRecords" in diag["diag:details"]


def test_sru_maximum_records_zero(client, document_sion_items):
    """Test SRU returns total count but no records when maximumRecords=0."""
    api_url = url_for(
        "api_sru.documents",
        version="1.1",
        operation="searchRetrieve",
        query='"La reine Berthe et son fils"',
        maximumRecords="0",
    )
    res = client.get(api_url)
    assert res.status_code == 200
    xml_dict = get_xml_dict(res)
    assert "zs:searchRetrieveResponse" in xml_dict
    search_rr = xml_dict["zs:searchRetrieveResponse"]
    assert int(search_rr["zs:numberOfRecords"]) >= 1
    assert "zs:records" not in search_rr or search_rr["zs:records"] == {}
    assert "zs:nextRecordPosition" not in search_rr
    echoed = search_rr["zs:echoedSearchRetrieveRequest"]
    assert echoed["zs:maximumRecords"] == "0"
    assert echoed["zs:operation"] == "searchRetrieve"


def test_sru_maximum_records_zero_dc(client, document_sion_items):
    """Test DC format returns total count but no records element when maximumRecords=0."""
    api_url = url_for(
        "api_sru.documents",
        version="1.1",
        operation="searchRetrieve",
        query='"La reine Berthe et son fils"',
        maximumRecords="0",
        format="dc",
    )
    res = client.get(api_url)
    assert res.status_code == 200
    xml_dict = get_xml_dict(res)
    assert "zs:searchRetrieveResponse" in xml_dict
    search_rr = xml_dict["zs:searchRetrieveResponse"]
    assert int(search_rr["zs:numberOfRecords"]) >= 1
    assert "zs:records" not in search_rr or search_rr["zs:records"] == {}
    echoed = search_rr["zs:echoedSearchRetrieveRequest"]
    assert echoed["zs:maximumRecords"] == "0"
    assert echoed["zs:resultSetTTL"] == "300"
    assert "zs:nextRecordPosition" not in search_rr


def test_sru_unknown_schema(client):
    """Test SRU returns diagnostic code 66 for an unrecognised recordSchema."""
    api_url = url_for(
        "api_sru.documents",
        version="1.1",
        operation="searchRetrieve",
        query="test",
        recordSchema="info:srw/schema/1/unknown",
    )
    res = client.get(api_url)
    assert res.status_code == 200
    xml_dict = get_xml_dict(res)
    assert "srw:searchRetrieveResponse" in xml_dict
    diag = xml_dict["srw:searchRetrieveResponse"]["srw:diagnostics"]["diag:diagnostic"]
    assert diag["diag:uri"] == "info:srw/diagnostic/1/66"
    assert diag["diag:message"] == "Unknown schema for retrieval"
    assert "info:srw/schema/1/unknown" in diag["diag:details"]


def test_sru_record_schema_echoed(client, document_sion_items):
    """Test SRU echoes back the canonical recordSchema URI in the response."""
    api_url = url_for(
        "api_sru.documents",
        version="1.1",
        operation="searchRetrieve",
        query='"La reine Berthe et son fils"',
        recordSchema="marcxml",
    )
    res = client.get(api_url)
    assert res.status_code == 200
    xml_dict = get_xml_dict(res)
    assert "zs:searchRetrieveResponse" in xml_dict
    echoed = xml_dict["zs:searchRetrieveResponse"]["zs:echoedSearchRetrieveRequest"]
    assert echoed["zs:recordSchema"] == SRU_MARCXML_SCHEMA_URI


def test_sru_next_record_position(client):
    """Test SRU emits nextRecordPosition at the response top level when more records exist."""
    from unittest.mock import patch

    from rero_ils.modules.sru.views import SRUDocumentsSearch

    api_url = url_for(
        "api_sru.documents",
        version="1.1",
        operation="searchRetrieve",
        query="books",
        startRecord="1",
        maximumRecords="5",
        format="dc",
    )
    with patch.object(SRUDocumentsSearch, "_execute_search", return_value=([], 20)):
        res = client.get(api_url)
    assert res.status_code == 200
    xml_dict = get_xml_dict(res)
    assert "zs:searchRetrieveResponse" in xml_dict
    search_rr = xml_dict["zs:searchRetrieveResponse"]
    assert search_rr["zs:numberOfRecords"] == "20"
    # nextRecordPosition must be a top-level sibling of records, not inside echoedSearchRetrieveRequest
    assert search_rr["zs:nextRecordPosition"] == "6"
    assert "zs:nextRecordPosition" not in search_rr.get("zs:echoedSearchRetrieveRequest", {})


def test_sru_result_set_created(sru_result_set_client, document_sion_items):
    """Test SRU includes resultSetId when RERO_ILS_SRU_RESULT_SET_TTL > 0."""
    api_url = url_for(
        "api_sru.documents",
        version="1.1",
        operation="searchRetrieve",
        query='"La reine Berthe et son fils"',
    )
    res = sru_result_set_client.get(api_url)
    assert res.status_code == 200
    xml_dict = get_xml_dict(res)
    search_rr = xml_dict["zs:searchRetrieveResponse"]
    assert "zs:resultSetId" in search_rr
    assert search_rr["zs:resultSetIdleTime"] == "60"


def test_sru_result_set_lookup(sru_result_set_client, document_sion_items):
    """Test SRU result set lookup returns the same record count as the original search."""
    # First request: save the result set and capture its ID
    api_url = url_for(
        "api_sru.documents",
        version="1.1",
        operation="searchRetrieve",
        query='"La reine Berthe et son fils"',
    )
    res1 = sru_result_set_client.get(api_url)
    assert res1.status_code == 200
    search_rr1 = get_xml_dict(res1)["zs:searchRetrieveResponse"]
    rsid = search_rr1["zs:resultSetId"]
    total1 = search_rr1["zs:numberOfRecords"]

    # Second request: reference the saved result set
    api_url2 = url_for(
        "api_sru.documents",
        version="1.1",
        operation="searchRetrieve",
        query=f'cql.resultSetId = "{rsid}"',
    )
    res2 = sru_result_set_client.get(api_url2)
    assert res2.status_code == 200
    search_rr2 = get_xml_dict(res2)["zs:searchRetrieveResponse"]
    assert search_rr2["zs:numberOfRecords"] == total1


def test_sru_result_set_preserves_sort(sru_result_set_client, document_sion_items):
    """Test that a result set lookup re-applies the sort order from the original query."""
    from unittest.mock import patch

    from rero_ils.modules.sru.views import SRUDocumentsSearch

    # First request with an explicit sort clause
    api_url = url_for(
        "api_sru.documents",
        version="1.1",
        operation="searchRetrieve",
        query='"La reine Berthe et son fils" sortBy dc.date/descending',
    )
    res1 = sru_result_set_client.get(api_url)
    assert res1.status_code == 200
    search_rr1 = get_xml_dict(res1)["zs:searchRetrieveResponse"]
    rsid = search_rr1["zs:resultSetId"]

    # Second request via resultSetId — capture the ES search dict
    captured = {}

    def capture_and_return(search, query):
        captured["search_dict"] = search.to_dict()
        return [], 0

    api_url2 = url_for(
        "api_sru.documents",
        version="1.1",
        operation="searchRetrieve",
        query=f'cql.resultSetId = "{rsid}"',
    )
    with patch.object(SRUDocumentsSearch, "_execute_search", side_effect=capture_and_return):
        res2 = sru_result_set_client.get(api_url2)

    assert res2.status_code == 200
    # The dc.date/descending sort must be preserved (maps to provisionActivity.startDate desc)
    assert "sort" in captured["search_dict"], "Sort must be present in result set lookup"
    assert any("provisionActivity.startDate" in str(s) for s in captured["search_dict"]["sort"])


def test_sru_result_set_not_found(client):
    """Test SRU returns diagnostic code 33 for an unknown or expired result set ID."""
    api_url = url_for(
        "api_sru.documents",
        version="1.1",
        operation="searchRetrieve",
        query='cql.resultSetId = "no-such-id"',
    )
    res = client.get(api_url)
    assert res.status_code == 200
    xml_dict = get_xml_dict(res)
    assert "srw:searchRetrieveResponse" in xml_dict
    diag = xml_dict["srw:searchRetrieveResponse"]["srw:diagnostics"]["diag:diagnostic"]
    assert diag["diag:uri"] == "info:srw/diagnostic/1/33"
    assert diag["diag:message"] == "Result set does not exist"
    assert "no-such-id" in diag["diag:details"]
