# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""SRU (Search/Retrieve via URL) REST API views.

This module implements the SRU 1.1 protocol endpoints for searching documents.
It provides a RESTful interface that accepts CQL queries and returns results
in MARCXML, Dublin Core, or JSON formats.

Supported Operations:
    - ``searchRetrieve``: Execute a CQL query and return matching documents
    - ``explain`` (default): Return server capabilities and supported indexes

Endpoint:
    GET /sru/documents

Query Parameters:
    - ``operation``: 'searchRetrieve' or omit for explain
    - ``query``: CQL query string (required for searchRetrieve)
    - ``startRecord``: First record to return (1-based, default: 1)
    - ``maximumRecords``: Max records to return (default: 100, max: 1000)
    - ``format``: Response format ('marcxml', 'dc', 'json')

Example:
    GET /sru/documents?operation=searchRetrieve&query=dc.title=python

See Also:
    - SRU Standard: http://www.loc.gov/standards/sru/
    - CQL Specification: http://www.loc.gov/standards/sru/cql/
"""

import hashlib
import uuid

from elasticsearch.exceptions import RequestError as ESRequestError
from flask import current_app
from flask import request as flask_request
from invenio_cache import current_cache
from invenio_rest import ContentNegotiatedMethodView
from werkzeug.exceptions import HTTPException
from werkzeug.wrappers import Response

from ..documents.api import DocumentsSearch, document_id_fetcher
from ..documents.serializers import (
    json_doc_search,
    xml_dc_search,
    xml_marcxmlsru_search,
)
from ..utils import strip_chars
from .cql_parser import SRU_DC_SCHEMA_URI, SRU_MARCXML_SCHEMA_URI, Diagnostic, parse
from .explain import Explain

#: Cache duration for Explain responses (1 hour in seconds).
#: Explain data changes rarely, only on deployment/configuration changes.
EXPLAIN_CACHE_MAX_AGE = 3600

#: Cache duration for searchRetrieve responses (60 seconds).
#: Search results may change as documents are added/updated/deleted.
SEARCH_CACHE_MAX_AGE = 60

#: Stale-while-revalidate duration for search responses (5 minutes).
#: Allows serving stale content while fetching fresh results in background.
SEARCH_STALE_WHILE_REVALIDATE = 300

#: Mapping from recordSchema parameter values (URIs and short names) to format aliases.
SUPPORTED_RECORD_SCHEMAS = {
    SRU_MARCXML_SCHEMA_URI: "marcxmlsru",
    "marcxml": "marcxmlsru",
    SRU_DC_SCHEMA_URI: "dc",
    "dc": "dc",
}

#: Canonical schema URI for each format alias, used for echoing in responses.
CANONICAL_RECORD_SCHEMA = {
    "marcxmlsru": SRU_MARCXML_SCHEMA_URI,
    "dc": SRU_DC_SCHEMA_URI,
}

#: Redis key prefix for stored SRU result sets.
_SRU_RSET_PREFIX = "sru:rset:"


def _save_result_set(query_cql, search_query, ttl, sort_keys=None, result_set_id=None):
    """Store a CQL search as a named result set and return its UUID.

    :param query_cql: Original CQL query string to associate with the result set.
    :param search_query: Search index query string for the search.
    :param ttl: Cache lifetime in seconds. 0 disables result set creation.
    :param sort_keys: Search index sort specifications to preserve across pages.
    :param result_set_id: Existing result set UUID to reuse; a fresh UUID is generated
        when ``None``.
    :returns: Result set UUID string, or ``None`` if TTL is zero.
    """
    if not ttl:
        return None
    rsid = result_set_id or str(uuid.uuid4())
    current_cache.set(
        f"{_SRU_RSET_PREFIX}{rsid}",
        {"query_cql": query_cql, "search_query": search_query, "sort_keys": sort_keys or []},
        timeout=ttl,
    )
    return rsid


def _load_result_set(rsid):
    """Retrieve a previously saved result set by its UUID.

    :param rsid: Result set UUID returned by :func:`_save_result_set`.
    :returns: ``{"query_cql": ..., "search_query": ..., "sort_keys": [...]}`` dict,
        or ``None`` if expired/unknown.
    """
    return current_cache.get(f"{_SRU_RSET_PREFIX}{rsid}")


def _generate_etag(content):
    """Generate an ETag hash from response content.

    :param content: The response body as string or bytes.
    :returns: A quoted ETag string suitable for use in HTTP headers.
    """
    if isinstance(content, str):
        content = content.encode("utf-8")
    return f'"{hashlib.md5(content, usedforsecurity=False).hexdigest()}"'


def _add_cache_headers(response, max_age, stale_while_revalidate=None, etag=None):
    """Add HTTP caching headers to a response.

    :param response: The Flask/Werkzeug Response object to modify.
    :param max_age: Cache duration in seconds for the ``max-age`` directive.
    :param stale_while_revalidate: Optional ``stale-while-revalidate`` duration in seconds.
    :param etag: Optional ETag value to set on the response.
    :returns: The response with caching headers added.
    """
    cache_control = f"public, max-age={max_age}"
    if stale_while_revalidate:
        cache_control += f", stale-while-revalidate={stale_while_revalidate}"
    response.headers["Cache-Control"] = cache_control
    if etag:
        response.headers["ETag"] = etag
    return response


def _parse_int_param(name, raw_value, query):
    """Parse an integer SRU query parameter, raising a diagnostic on failure.

    :param name: parameter name used in the error detail.
    :param raw_value: raw string value from the request.
    :param query: original CQL query string for the diagnostic.
    :returns: parsed integer value.
    :raises HTTPException: with SRU diagnostic code 6 if not a valid integer.
    """
    try:
        return int(raw_value)
    except ValueError as exc:
        raise HTTPException(
            response=_diagnostic_response(
                Diagnostic(
                    code=6,
                    message="Unsupported parameter value",
                    details=f"{name}: {raw_value!r} is not a valid integer",
                    query=query,
                )
            )
        ) from exc


def _diagnostic_response(diag):
    """Build an XML ``Response`` from a ``Diagnostic`` instance.

    :param diag: the Diagnostic exception to serialise.
    :returns: a Werkzeug Response with content-type application/xml.
    """
    response = Response(diag.xml_str())
    response.headers["content-type"] = "application/xml"
    return response


class SRUDocumentsSearch(ContentNegotiatedMethodView):
    """SRU search REST resource for documents.

    Implements the SRU 1.1 protocol for searching the documents index.
    Supports content negotiation for multiple output formats.

    Supported Media Types:
        - ``application/xml``: MARCXML-SRU format (default)
        - ``application/xml+dc``: Dublin Core XML format
        - ``application/rero+json``: RERO-ILS JSON format

    Format Aliases:
        Use the ``format`` query parameter with: 'marcxmlsru', 'dc', or 'json'
    """

    def __init__(self, **kwargs):
        """Initialize the SRU search view with content negotiation settings.

        :param kwargs: Additional arguments passed to
            :class:`~invenio_rest.ContentNegotiatedMethodView`.
        """
        super().__init__(
            method_serializers={
                "GET": {
                    "application/xml": xml_marcxmlsru_search,
                    "application/xml+dc": xml_dc_search,
                    "application/rero+json": json_doc_search,
                }
            },
            serializers_query_aliases={
                "marcxmlsru": "application/xml",
                "dc": "application/xml+dc",
                "json": "application/rero+json",
            },
            default_method_media_type={"GET": "application/xml"},
            default_media_type="application/xml",
            **kwargs,
        )

    def match_serializers(self, serializers, default_media_type):
        """Select a serializer, giving precedence to the SRU ``recordSchema`` parameter.

        If the client supplies a recognised ``recordSchema`` value it takes priority
        over the ``format`` query parameter so that standard SRU clients can select
        the output schema without knowing RERO-ILS's custom ``format`` extension.

        :param serializers: Dict of mime-type → serializer callable.
        :param default_media_type: Fallback mime type when no match is found.
        :returns: The matching serializer callable, or ``None``.
        """
        record_schema = flask_request.args.get("recordSchema")
        if record_schema and record_schema in SUPPORTED_RECORD_SCHEMAS:
            fmt = SUPPORTED_RECORD_SCHEMAS[record_schema]
            mime = self.serializers_query_aliases[fmt]
            return serializers.get(mime)
        return super().match_serializers(serializers, default_media_type)

    def get(self, **kwargs):
        """Handle GET requests to the SRU endpoint.

        Dispatches to :meth:`_search_retrieve` or :meth:`_explain` after
        validating the common query parameters.

        Raises:
            HTTPException: On validation failure or when returning any SRU
                response (both success and error paths use HTTPException so
                that Flask skips further processing).
        """
        operation = flask_request.args.get("operation", None)
        cql_query = flask_request.args.get("query", None)

        # TODO: implement the SRU 'scan' operation (index term browsing).
        # See http://www.loc.gov/standards/sru/sru-1-1.html#scan for the spec.
        # The CQL parser (cheshire3 port) already handles the grammar; the remaining
        # work is: (1) request validation (scanClause, responsePosition, maximumTerms),
        # (2) ES terms-aggregation query, (3) scanResponse XML serialization.
        #
        # Blocker: most useful scan targets (dc.title, dc.subject, dc.creator,
        # dc.publisher, dc.description, ...) are plain `text` fields in the document
        # mapping with no `.raw`/`.keyword` sub-field, so ES cannot aggregate them.
        # Fields that can be used in a terms aggregation without a mapping change:
        #   - keyword fields: contribution.role, language.value, type.main_type,
        #     type.subtype, contentMediaCarrier.*Type, org_pid, library_pid,
        #     holdings.location.pid
        #   - has .raw sub-field: identifiedBy.value (use identifiedBy.value.raw)
        # To support the remaining fields, add `.raw` keyword sub-fields to the
        # relevant text fields in document-v0.0.1.json and reindex documents.
        if operation is not None and operation not in ("searchRetrieve", "explain"):
            raise HTTPException(
                response=_diagnostic_response(
                    Diagnostic(code=4, message="Unsupported operation", details=operation, query=cql_query or "")
                )
            )

        # Validate version (code 5: unsupported version)
        version = flask_request.args.get("version", None)
        if version is not None and version != "1.1":
            raise HTTPException(
                response=_diagnostic_response(
                    Diagnostic(code=5, message="Unsupported version", details=version, query=cql_query or "")
                )
            )

        # Validate recordPacking (code 6: unsupported parameter value) — only xml supported
        record_packing = flask_request.args.get("recordPacking", None)
        if record_packing is not None and record_packing.lower() != "xml":
            raise HTTPException(
                response=_diagnostic_response(
                    Diagnostic(
                        code=6,
                        message="Unsupported parameter value",
                        details=f"recordPacking: {record_packing!r} is not supported (only 'xml')",
                        query=cql_query or "",
                    )
                )
            )

        # Validate recordSchema (code 66: unknown schema for retrieval)
        record_schema_param = flask_request.args.get("recordSchema", None)
        if record_schema_param is not None and record_schema_param not in SUPPORTED_RECORD_SCHEMAS:
            raise HTTPException(
                response=_diagnostic_response(
                    Diagnostic(
                        code=66,
                        message="Unknown schema for retrieval",
                        details=record_schema_param,
                        query=cql_query or "",
                    )
                )
            )
        # Resolve canonical schema URI for echoing in responses.
        # recordSchema takes precedence; fall back to the format param.
        if record_schema_param:
            canonical_schema = CANONICAL_RECORD_SCHEMA[SUPPORTED_RECORD_SCHEMAS[record_schema_param]]
        else:
            fmt = flask_request.args.get("format", "marcxmlsru")
            canonical_schema = CANONICAL_RECORD_SCHEMA.get(fmt, SRU_MARCXML_SCHEMA_URI)

        # Validate startRecord (code 6: must be a positive integer)
        start_record = _parse_int_param("startRecord", flask_request.args.get("startRecord", "1"), cql_query or "")
        if start_record < 1:
            raise HTTPException(
                response=_diagnostic_response(
                    Diagnostic(
                        code=6,
                        message="Unsupported parameter value",
                        details=f"startRecord: {start_record} must be 1 or greater",
                        query=cql_query or "",
                    )
                )
            )

        # Validate maximumRecords (code 6: must be a non-negative integer); 0 is valid (returns count only)
        default_max = current_app.config.get("RERO_ILS_SRU_NUMBER_OF_RECORDS", 100)
        maximum_records = _parse_int_param(
            "maximumRecords", flask_request.args.get("maximumRecords", str(default_max)), cql_query or ""
        )
        if maximum_records < 0:
            raise HTTPException(
                response=_diagnostic_response(
                    Diagnostic(
                        code=6,
                        message="Unsupported parameter value",
                        details=f"maximumRecords: {maximum_records} must be 0 or greater",
                        query=cql_query or "",
                    )
                )
            )
        maximum_records = min(maximum_records, current_app.config.get("RERO_ILS_SRU_MAXIMUM_RECORDS", 1000))

        if operation == "searchRetrieve":
            return self._search_retrieve(cql_query, start_record, maximum_records, canonical_schema)
        raise HTTPException(response=self._explain())

    def _search_retrieve(self, query, start_record, maximum_records, record_schema):
        """Execute a CQL searchRetrieve operation and return a response.

        :param query: raw CQL query string from the request.
        :param start_record: 1-based first record index (already validated).
        :param maximum_records: maximum number of records to return (already validated).
        :param record_schema: canonical schema URI to echo in the response.
        :raises HTTPException: on missing query, CQL parse error, or ES error.
        """
        if not query:
            raise HTTPException(
                response=_diagnostic_response(
                    Diagnostic(code=7, message="Mandatory parameter not supplied", details="query", query="")
                )
            )
        try:
            parsed_query = parse(query)
            if rsid_ref := parsed_query.get_result_set_id():
                stored = _load_result_set(rsid_ref)
                if stored is None:
                    raise Diagnostic(code=33, message="Result set does not exist", details=rsid_ref, query=query)
                query_string = stored["search_query"]
                save_cql = stored["query_cql"]
                sort_keys = stored.get("sort_keys", [])
            else:
                query_string = parsed_query.to_search()
                save_cql = strip_chars(query)
                sort_keys = parsed_query.get_search_sort()
        except Diagnostic as err:
            raise HTTPException(response=_diagnostic_response(err)) from err

        search = (
            DocumentsSearch()
            .query("query_string", query=query_string)
            .exclude("term", _masked=True)
            .exclude("term", _draft=True)
        )
        if sort_keys:
            search = search.sort(*sort_keys)
        search = search[(start_record - 1) : maximum_records + (start_record - 1)]

        records, total = self._execute_search(search, query)

        result_set_ttl = current_app.config.get("RERO_ILS_SRU_RESULT_SET_TTL", 0)
        result_set_id = _save_result_set(save_cql, query_string, result_set_ttl, sort_keys, rsid_ref or None)

        result = {
            "hits": {
                "hits": records,
                "total": {"value": total, "relation": "eq"},
                "sru": {
                    "operation": "searchRetrieve",
                    "cql_query": strip_chars(query),
                    "search_query": query_string,
                    "start_record": start_record,
                    "maximum_records": maximum_records,
                    "record_schema": record_schema,
                    "result_set_id": result_set_id,
                    "result_set_ttl": result_set_ttl,
                },
            }
        }
        response = self.make_response(pid_fetcher=document_id_fetcher, search_result=result)
        response.headers["Vary"] = "Accept"
        _add_cache_headers(response, max_age=SEARCH_CACHE_MAX_AGE, stale_while_revalidate=SEARCH_STALE_WHILE_REVALIDATE)
        return response

    def _execute_search(self, search, query):
        """Run the ES search and return ``(records, total)``.

        :param search: prepared :class:`DocumentsSearch` instance.
        :param query: original CQL string, used in diagnostic messages.
        :raises HTTPException: on fatal ES errors.
        """
        try:
            response = search.execute()
            records = [
                {"_id": hit.meta.id, "_index": hit.meta.index, "_source": hit.to_dict(), "_version": 0}
                for hit in response
            ]
            total = getattr(response.hits.total, "value", response.hits.total)
            return records, total
        except ESRequestError as e:
            err_text = str(getattr(e, "info", e))
            if "Result window" in err_text or "result_window" in err_text:
                current_app.logger.warning(f"ES window overflow during SRU search: {e}")
                return [], 0
            current_app.logger.error(f"ES backend error during SRU search: {e}")
            raise HTTPException(
                response=_diagnostic_response(
                    Diagnostic(code=2, message="System temporarily unavailable", details=str(e), query=query)
                )
            ) from e

    def _explain(self):
        """Build and return the SRU Explain XML response.

        Handles conditional GET (``If-None-Match``) and attaches cache headers.

        :returns: a Werkzeug :class:`Response` ready to be raised as an
            :class:`HTTPException`.
        """
        content = str(Explain("api/sru/documents"))
        etag = _generate_etag(content)
        if_none_match = flask_request.headers.get("If-None-Match", "")
        client_etags = [e.strip() for e in if_none_match.split(",")]
        if etag in client_etags or "*" in client_etags:
            not_modified = Response(status=304)
            not_modified.headers["ETag"] = etag
            not_modified.headers["Cache-Control"] = f"public, max-age={EXPLAIN_CACHE_MAX_AGE}"
            not_modified.headers["Vary"] = "Accept"
            return not_modified
        response = Response(content)
        response.headers["Content-Type"] = "application/xml"
        response.headers["Vary"] = "Accept"
        _add_cache_headers(response, max_age=EXPLAIN_CACHE_MAX_AGE, etag=etag)
        return response
