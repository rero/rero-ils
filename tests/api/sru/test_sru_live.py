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

"""Live SRU CQL and sort retrieval tests against a running server.

Run with:
    uv run pytest tests/api/sru/test_sru_live.py -v -m external
"""

import pytest
import requests
import xmltodict

BASE_URL = "https://127.0.0.1:5000/api/sru/documents"
DOC_API_URL = "https://127.0.0.1:5000/api/documents"

# PID of a well-known stable fixture document (https://127.0.0.1:5000/api/sru/documents?version=1.1&operation=searchRetrieve&query=dc.title=%22Les%20voyages%20de%20Gulliver%22%20AND%20dc.organisation=3&maximumRecords=3)
FIXTURE_PID = "100"


def sru(query, maximum_records=3, start_record=1, fmt=None):
    """Perform a searchRetrieve request and return the parsed XML dict."""
    params = {
        "version": "1.1",
        "operation": "searchRetrieve",
        "query": query,
        "maximumRecords": maximum_records,
        "startRecord": start_record,
    }
    if fmt:
        params["format"] = fmt
    resp = requests.get(BASE_URL, params=params, verify=False, timeout=10)
    assert resp.status_code == 200, f"HTTP {resp.status_code}: {resp.text[:200]}"
    return xmltodict.parse(resp.text)


def fetch_json(pid):
    """Fetch the canonical document JSON from the REST API."""
    resp = requests.get(f"{DOC_API_URL}/{pid}", verify=False, timeout=10)
    assert resp.status_code == 200, f"HTTP {resp.status_code} for /api/documents/{pid}"
    return resp.json()["metadata"]


def marc_subfields(datafield, code):
    """Return a list of subfield values for *code* from a MARC datafield dict."""
    subs = datafield.get("subfield", [])
    if isinstance(subs, dict):
        subs = [subs]
    return [s["#text"] for s in subs if s.get("@code") == code]


def marc_fields(record, tag):
    """Return a list of datafield dicts whose @tag matches *tag*."""
    fields = record.get("datafield", [])
    if isinstance(fields, dict):
        fields = [fields]
    return [f for f in fields if f.get("@tag") == tag]


def marc_controlfield(record, tag):
    """Return the text of the controlfield with *tag*, or None."""
    cfs = record.get("controlfield", [])
    if isinstance(cfs, dict):
        cfs = [cfs]
    return next((cf["#text"] for cf in cfs if cf.get("@tag") == tag), None)


def first_sru_marc_record(sru_xml):
    """Extract the first MARC record from a zs: searchRetrieveResponse."""
    records_container = (sru_xml.get("zs:searchRetrieveResponse") or {}).get("zs:records")
    if not records_container:
        pytest.fail("no SRU records in response (zs:records missing or empty)")
    recs = records_container.get("zs:record")
    if not recs:
        pytest.fail("no SRU records in response (zs:record missing or empty)")
    if isinstance(recs, dict):
        recs = [recs]
    return recs[0]["zs:recordData"]["record"]


def first_sru_dc_record(sru_xml):
    """Extract the DC record dict from a searchRetrieveResponse."""
    records_container = (sru_xml.get("searchRetrieveResponse") or {}).get("records")
    if not records_container:
        pytest.fail("no SRU records in response (records missing or empty)")
    recs = records_container.get("record")
    if not recs:
        pytest.fail("no SRU records in response (record missing or empty)")
    if isinstance(recs, dict):
        recs = [recs]
    return recs[0]


def echoed(xml):
    """Return the echoedSearchRetrieveRequest block (works for zs: and srw: prefixes)."""
    root = xml.get("zs:searchRetrieveResponse") or xml.get("srw:searchRetrieveResponse") or {}
    return root.get("zs:echoedSearchRetrieveRequest") or root.get("srw:echoedSearchRetrieveRequest") or {}


def n_records(xml):
    """Return numberOfRecords as int (works for zs: and srw: prefixes)."""
    root = xml.get("zs:searchRetrieveResponse") or xml.get("srw:searchRetrieveResponse") or {}
    return int(root.get("zs:numberOfRecords") or root.get("srw:numberOfRecords") or 0)


def diagnostic(xml):
    """Return the diagnostic block if present, else None."""
    root = xml.get("srw:searchRetrieveResponse") or xml.get("zs:searchRetrieveResponse") or {}
    return root.get("diag:diagnostics")


# ---------------------------------------------------------------------------
# Fixtures / markers
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def _check_server():
    """Skip all tests in this module if the server is not reachable."""
    try:
        requests.get(BASE_URL, verify=False, timeout=3)
    except requests.exceptions.ConnectionError:
        pytest.skip(f"SRU server not reachable at {BASE_URL}")


# ---------------------------------------------------------------------------
# CQL index mapping tests
# ---------------------------------------------------------------------------


@pytest.mark.external
@pytest.mark.usefixtures("_check_server")
class TestCQLIndexMappings:
    """Verify that each DC index is translated to the correct search field."""

    def test_serverchoice(self):
        """Bare term uses server-choice (no field prefix in search query)."""
        xml = sru("swift")
        assert echoed(xml)["zs:search_query"] == "swift"

    def test_quoted_term(self):
        """Quoted phrase is passed through as-is."""
        xml = sru('"Les voyages de Gulliver"')
        assert echoed(xml)["zs:search_query"] == '"Les voyages de Gulliver"'
        assert n_records(xml) >= 1

    def test_dc_title(self):
        """dc.title maps to title.* wildcard field."""
        xml = sru("dc.title=Gulliver")
        assert echoed(xml)["zs:search_query"] == r"title.\*:Gulliver"
        assert n_records(xml) >= 1

    def test_dc_title_quoted(self):
        """Quoted dc.title phrase is preserved in the search query."""
        xml = sru('dc.title="Les voyages de Gulliver"')
        assert echoed(xml)["zs:search_query"] == r'title.\*:"Les voyages de Gulliver"'
        assert n_records(xml) >= 1

    def test_dc_creator(self):
        """dc.creator maps to contribution role + authorized_access_point."""
        xml = sru("dc.creator=Swift")
        es = echoed(xml)["zs:search_query"]
        assert "authorized_access_point:Swift" in es
        assert "cre" in es  # creator role must be in the role list

    def test_dc_language(self):
        """dc.language maps to language.value."""
        xml = sru("dc.language=fre", maximum_records=1)
        assert echoed(xml)["zs:search_query"] == "language.value:fre"
        assert n_records(xml) >= 1

    def test_dc_publisher(self):
        """dc.publisher maps to provisionActivity publication statement."""
        xml = sru("dc.publisher=Edito", maximum_records=1)
        es = echoed(xml)["zs:search_query"]
        assert "provisionActivity" in es
        assert "Edito" in es

    def test_dc_type(self):
        """dc.type maps to type.main_type."""
        xml = sru("dc.type=docmaintype_book", maximum_records=1)
        assert echoed(xml)["zs:search_query"] == "type.main_type:docmaintype_book"

    def test_dc_organisation(self):
        """dc.organisation maps to organisation_pid."""
        xml = sru("dc.organisation=3", maximum_records=1)
        assert echoed(xml)["zs:search_query"] == "organisation_pid:3"


# ---------------------------------------------------------------------------
# Boolean operator tests
# ---------------------------------------------------------------------------


@pytest.mark.external
@pytest.mark.usefixtures("_check_server")
class TestCQLBooleans:
    """Verify AND / OR boolean combinations."""

    def test_and_title_organisation(self):
        """AND combines two clauses with parentheses in search."""
        xml = sru('dc.title="Les voyages de Gulliver" AND dc.organisation=3')
        es = echoed(xml)["zs:search_query"]
        assert es == r'(title.\*:"Les voyages de Gulliver" AND organisation_pid:3)'
        assert n_records(xml) == 1

    def test_and_title_type(self):
        """AND with type filter narrows results correctly."""
        xml = sru("dc.title=Gulliver AND dc.type=docmaintype_book")
        es = echoed(xml)["zs:search_query"]
        assert r"title.\*:Gulliver" in es
        assert "type.main_type:docmaintype_book" in es

    def test_or_titles(self):
        """OR expands the result set."""
        xml_and = sru("dc.title=Gulliver AND dc.title=Swift")
        xml_or = sru("dc.title=Gulliver OR dc.title=Swift")
        n_and = n_records(xml_and)
        n_or = n_records(xml_or)
        assert n_or >= n_and  # OR always returns at least as many as AND

    def test_triple_and(self):
        """Three-clause AND wraps correctly."""
        xml = sru('dc.title="Les voyages de Gulliver" AND dc.organisation=3 AND dc.language=fre')
        es = echoed(xml)["zs:search_query"]
        assert r'title.\*:"Les voyages de Gulliver"' in es
        assert "organisation_pid:3" in es
        assert "language.value:fre" in es


# ---------------------------------------------------------------------------
# Sort tests
# ---------------------------------------------------------------------------


@pytest.mark.external
@pytest.mark.usefixtures("_check_server")
class TestCQLSort:
    """Verify sortBy clauses are accepted and echoed correctly."""

    def test_sort_by_title_ascending(self):
        """SortBy dc.title maps sort_title ascending."""
        xml = sru("dc.language=fre sortBy dc.title/ascending", maximum_records=3)
        ech = echoed(xml)
        # Query part strips the sort clause
        assert "sortBy" not in ech["zs:search_query"]
        # Results are returned
        assert n_records(xml) >= 1

    def test_sort_by_title_descending(self):
        """SortBy dc.title/descending is valid."""
        xml = sru("dc.language=fre sortBy dc.title/descending", maximum_records=3)
        assert n_records(xml) >= 1
        assert "sortBy" not in echoed(xml)["zs:search_query"]

    def test_sort_by_date_descending(self):
        """SortBy dc.date/descending maps provisionActivity.startDate desc."""
        xml = sru("dc.title=Gulliver sortBy dc.date/descending")
        assert n_records(xml) >= 1
        assert "sortBy" not in echoed(xml)["zs:search_query"]

    def test_sort_by_date_ascending(self):
        """SortBy dc.date/ascending is valid."""
        xml = sru("dc.language=fre sortBy dc.date/ascending", maximum_records=3)
        assert n_records(xml) >= 1

    def test_sort_by_relevance(self):
        """SortBy _relevance maps to _score."""
        xml = sru("dc.title=Gulliver sortBy _relevance")
        assert n_records(xml) >= 1
        assert "sortBy" not in echoed(xml)["zs:search_query"]

    def test_sort_multi_key(self):
        """Multiple sort keys (dc.title then dc.date) are accepted."""
        xml = sru("swift sortBy dc.title/ascending dc.date/descending", maximum_records=3)
        assert n_records(xml) >= 1
        assert "sortBy" not in echoed(xml)["zs:search_query"]

    def test_sort_with_boolean(self):
        """Sort clause works together with a boolean AND query."""
        xml = sru("dc.title=Gulliver AND dc.language=fre sortBy dc.title", maximum_records=3)
        es = echoed(xml)["zs:search_query"]
        assert r"title.\*:Gulliver" in es
        assert "sortBy" not in es


# ---------------------------------------------------------------------------
# Diagnostic / error tests
# ---------------------------------------------------------------------------


@pytest.mark.external
@pytest.mark.usefixtures("_check_server")
class TestCQLDiagnostics:
    """Verify that invalid CQL returns the correct SRU diagnostic."""

    def test_malformed_query(self):
        """Unbalanced parentheses returns Diagnostic 10 (Malformed Query)."""
        xml = sru("(((")
        diag = diagnostic(xml)
        assert diag is not None
        assert diag["diag:message"] == "Malformed Query"
        assert diag["diag:uri"] == "info:srw/diagnostic/1/10"

    def test_unsupported_relation_modifier(self):
        """Using /stem modifier returns Diagnostic 21."""
        xml = sru("dc.title all/stem Gulliver")
        diag = diagnostic(xml)
        assert diag is not None
        assert diag["diag:uri"] == "info:srw/diagnostic/1/21"
        assert "stem" in diag["diag:details"]

    def test_empty_index(self):
        """A leading dot in the index name returns a diagnostic."""
        xml = sru(".title=Gulliver")
        diag = diagnostic(xml)
        assert diag is not None  # Null indexset error

    def test_valid_query_no_diagnostic(self):
        """A well-formed query returns no diagnostic."""
        xml = sru("dc.title=Gulliver")
        assert diagnostic(xml) is None
        assert "zs:searchRetrieveResponse" in xml


# ---------------------------------------------------------------------------
# MARCXML conversion tests — cross-checked against /api/documents/{pid}
# ---------------------------------------------------------------------------


@pytest.mark.external
@pytest.mark.usefixtures("_check_server")
class TestMARCXMLConversion:
    """Verify MARCXML output against the canonical document JSON."""

    @pytest.fixture(scope="class")
    def doc_json(self, marc_record):
        """Canonical JSON for the same document as marc_record (PID from 001)."""
        pid = marc_controlfield(marc_record, "001")
        return fetch_json(pid)

    @pytest.fixture(scope="class")
    def marc_record(self):
        """First MARC record from the SRU MARCXML response."""
        xml = sru('dc.title="Les voyages de Gulliver" AND dc.organisation=3', maximum_records=1)
        return first_sru_marc_record(xml)

    def test_controlfield_001_matches_pid(self, doc_json, marc_record):
        """MARC 001 (record ID) must equal the document PID."""
        assert marc_controlfield(marc_record, "001") == doc_json["pid"]

    def test_controlfield_008_language(self, doc_json, marc_record):
        """MARC 008 positions 35-37 must carry the primary language code."""
        field_008 = marc_controlfield(marc_record, "008")
        assert field_008 is not None, "008 field missing"
        lang_in_json = doc_json["language"][0]["value"]
        # positions 35-37 in 008
        assert field_008[35:38] == lang_in_json

    def test_field_245_main_title(self, doc_json, marc_record):
        """MARC 245 $a must match the first mainTitle value from JSON."""
        json_title = doc_json["title"][0]["mainTitle"][0]["value"]
        fields_245 = marc_fields(marc_record, "245")
        assert fields_245, "245 field missing"
        subfield_a = marc_subfields(fields_245[0], "a")
        assert subfield_a, "245 $a missing"
        assert subfield_a[0] == json_title

    def test_field_264_publication_date(self, doc_json, marc_record):
        """MARC 264 ind2=1 $c must contain the publication year from JSON."""
        json_date = str(doc_json["provisionActivity"][0]["startDate"])
        pub_fields = [f for f in marc_fields(marc_record, "264") if f.get("@ind2") == "1"]
        assert pub_fields, "264 ind2=1 field missing"
        dates = marc_subfields(pub_fields[0], "c")
        assert any(json_date in d for d in dates), f"{json_date} not found in 264 $c: {dates}"

    def test_field_264_publisher(self, doc_json, marc_record):
        """MARC 264 ind2=1 $b must match the publisher from JSON."""
        # Extract publisher name from provisionActivity statements
        statements = doc_json["provisionActivity"][0].get("statement", [])
        json_publisher = next(
            (s["label"][0]["value"] for s in statements if s.get("type") == "bf:Agent"),
            None,
        )
        assert json_publisher is not None, "No publisher in JSON"
        pub_fields = [f for f in marc_fields(marc_record, "264") if f.get("@ind2") == "1"]
        publishers = marc_subfields(pub_fields[0], "b")
        assert any(json_publisher in p for p in publishers), (
            f"Publisher '{json_publisher}' not found in 264 $b: {publishers}"
        )

    def test_field_300_extent(self, doc_json, marc_record):
        """MARC 300 $a must match the extent from JSON."""
        json_extent = doc_json["extent"]
        fields_300 = marc_fields(marc_record, "300")
        assert fields_300, "300 field missing"
        extents = marc_subfields(fields_300[0], "a")
        assert extents, "300 $a missing"
        assert extents[0] == json_extent

    def test_field_300_dimensions(self, doc_json, marc_record):
        """MARC 300 $c must match the first dimension from JSON."""
        json_dim = doc_json["dimensions"][0]
        fields_300 = marc_fields(marc_record, "300")
        dims = marc_subfields(fields_300[0], "c")
        assert dims, "300 $c missing"
        assert dims[0] == json_dim

    def test_field_700_creator_role(self, doc_json, marc_record):
        """MARC 700 with $4=cre must be present for the creator contribution."""
        creator_roles = [c["role"] for c in doc_json["contribution"] if "cre" in c["role"]]
        assert creator_roles, "No creator in JSON"
        fields_700 = marc_fields(marc_record, "700")
        cre_fields = [f for f in fields_700 if "cre" in marc_subfields(f, "4")]
        assert cre_fields, "No 700 $4=cre in MARCXML"

    def test_field_900_document_type(self, doc_json, marc_record):
        """MARC 900 $a must carry the main document type from JSON."""
        json_type = doc_json["type"][0]["main_type"]
        fields_900 = marc_fields(marc_record, "900")
        assert fields_900, "900 field missing"
        types_a = marc_subfields(fields_900[0], "a")
        assert any(json_type.lower() in t.lower() for t in types_a), (
            f"Type '{json_type}' not found in 900 $a: {types_a}"
        )


# ---------------------------------------------------------------------------
# Dublin Core conversion tests — cross-checked against /api/documents/{pid}
# ---------------------------------------------------------------------------


@pytest.mark.external
@pytest.mark.usefixtures("_check_server")
class TestDCConversion:
    """Verify Dublin Core output against the canonical document JSON."""

    @pytest.fixture(scope="class")
    def doc_json(self):
        """Canonical JSON from /api/documents/FIXTURE_PID."""
        return fetch_json(FIXTURE_PID)

    @pytest.fixture(scope="class")
    def dc_record(self):
        """DC record dict from the SRU DC response."""
        xml = sru(f"dc.identifier={FIXTURE_PID}", maximum_records=1, fmt="dc")
        return first_sru_dc_record(xml)

    def test_dc_title_contains_main_title(self, doc_json, dc_record):
        """dc:title must start with the document's main title."""
        json_title = doc_json["title"][0]["mainTitle"][0]["value"]
        assert dc_record["dc:title"].startswith(json_title), (
            f"dc:title '{dc_record['dc:title']}' does not start with '{json_title}'"
        )

    def test_dc_language(self, doc_json, dc_record):
        """dc:language must match the primary language code from JSON."""
        json_lang = doc_json["language"][0]["value"]
        assert dc_record["dc:language"] == json_lang

    def test_dc_date(self, doc_json, dc_record):
        """dc:date must equal the publication start year from JSON."""
        json_date = str(doc_json["provisionActivity"][0]["startDate"])
        assert dc_record["dc:date"] == json_date

    def test_dc_publisher(self, doc_json, dc_record):
        """dc:publisher must match the publisher name from JSON."""
        statements = doc_json["provisionActivity"][0].get("statement", [])
        json_publisher = next(
            (s["label"][0]["value"] for s in statements if s.get("type") == "bf:Agent"),
            None,
        )
        assert json_publisher is not None, "No publisher in JSON"
        assert dc_record["dc:publisher"] == json_publisher

    def test_dc_identifier_contains_pid(self, doc_json, dc_record):
        """dc:identifier must include an entry carrying the document PID."""
        pid = doc_json["pid"]
        identifiers = dc_record["dc:identifier"]
        if isinstance(identifiers, str):
            identifiers = [identifiers]
        assert any(pid in ident for ident in identifiers), f"PID '{pid}' not found in dc:identifier: {identifiers}"

    def test_dc_type_contains_main_type(self, doc_json, dc_record):
        """dc:type must mention the document's main type."""
        json_type = doc_json["type"][0]["main_type"].replace("docmaintype_", "")
        dc_type = dc_record.get("dc:type", "")
        assert json_type in dc_type.lower(), f"Main type '{json_type}' not found in dc:type '{dc_type}'"
