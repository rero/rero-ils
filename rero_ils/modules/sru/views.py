# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
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

from elasticsearch.exceptions import RequestError as ESRequestError
from flask import current_app
from flask import request as flask_request
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
from .cql_parser import Diagnostic, parse
from .explaine import Explain

#: Cache duration for Explain responses (1 hour in seconds).
#: Explain data changes rarely, only on deployment/configuration changes.
EXPLAIN_CACHE_MAX_AGE = 3600

#: Cache duration for searchRetrieve responses (60 seconds).
#: Search results may change as documents are added/updated/deleted.
SEARCH_CACHE_MAX_AGE = 60

#: Stale-while-revalidate duration for search responses (5 minutes).
#: Allows serving stale content while fetching fresh results in background.
SEARCH_STALE_WHILE_REVALIDATE = 300


def _generate_etag(content):
    """Generate an ETag hash from response content.

    Args:
        content: The response body as string or bytes.

    Returns:
        A quoted ETag string suitable for HTTP headers.
    """
    if isinstance(content, str):
        content = content.encode("utf-8")
    return f'"{hashlib.md5(content, usedforsecurity=False).hexdigest()}"'


def _add_cache_headers(response, max_age, stale_while_revalidate=None, etag=None):
    """Add HTTP caching headers to a response.

    Args:
        response: The Flask/Werkzeug Response object.
        max_age: Cache duration in seconds.
        stale_while_revalidate: Optional duration for stale-while-revalidate.
        etag: Optional ETag value for conditional requests.

    Returns:
        The response with caching headers added.
    """
    cache_control = f"public, max-age={max_age}"
    if stale_while_revalidate:
        cache_control += f", stale-while-revalidate={stale_while_revalidate}"
    response.headers["Cache-Control"] = cache_control
    if etag:
        response.headers["ETag"] = etag
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

        Args:
            **kwargs: Additional arguments passed to ContentNegotiatedMethodView.
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

    def get(self, **kwargs):
        """Handle GET requests to the SRU endpoint.

        Processes SRU searchRetrieve and explain operations. For searchRetrieve,
        parses the CQL query, executes it against Elasticsearch, and returns
        results in the requested format. For explain (or when no operation is
        specified), returns the server's capabilities.

        Args:
            **kwargs: Additional arguments from the URL route.

        Returns:
            A Flask response with search results or explain information.
            Content-Type depends on format requested (XML or JSON).

        Raises:
            HTTPException: When CQL parsing fails, returns an XML diagnostic
                response with the error details.
        """
        operation = flask_request.args.get("operation", None)
        query = flask_request.args.get("query", None)
        start_record = max(int(flask_request.args.get("startRecord", 1)), 1)
        maximum_records = min(
            int(
                flask_request.args.get(
                    "maximumRecords",
                    current_app.config.get("RERO_ILS_SRU_NUMBER_OF_RECORDS", 100),
                )
            ),
            current_app.config.get("RERO_ILS_SRU_MAXIMUM_RECORDS", 1000),
        )
        if operation == "searchRetrieve" and query:
            try:
                parsed_query = parse(query)
                query_string = parsed_query.to_es()
                # Extract sort keys if present
                sort_keys = parsed_query.get_es_sort()
            except Diagnostic as err:
                response = Response(err.xml_str())
                response.headers["content-type"] = "application/xml"
                raise HTTPException(response=response) from err

            search = (
                DocumentsSearch()
                .query("query_string", query=query_string)
                .exclude("term", _masked=True)
                .exclude("term", _draft=True)
            )
            # Apply sort if specified in CQL query
            if sort_keys:
                search = search.sort(*sort_keys)
            records = []
            total = 0
            search = search[(start_record - 1) : maximum_records + (start_record - 1)]
            try:
                response = search.execute()
                for hit in response:
                    records.append(
                        {
                            "_id": hit.meta.id,
                            "_index": hit.meta.index,
                            "_source": hit.to_dict(),
                            "_version": 0,
                        }
                    )
                total = response.hits.total.value if hasattr(response.hits.total, "value") else response.hits.total
            except ESRequestError as e:
                _err_text = str(getattr(e, "info", e))
                if "Result window" in _err_text or "result_window" in _err_text:
                    # startRecord window exceeds ES max_result_window; return 0 records.
                    current_app.logger.warning(f"ES window overflow during SRU search: {e}")
                else:
                    current_app.logger.error(f"ES backend error during SRU search: {e}")
                    diag = Diagnostic(
                        code=2,
                        message="System temporarily unavailable",
                        details=str(e),
                        query=query,
                    )
                    diag_response = Response(diag.xml_str())
                    diag_response.headers["content-type"] = "application/xml"
                    raise HTTPException(response=diag_response) from e

            result = {
                "hits": {
                    "hits": records,
                    "total": {"value": total, "relation": "eq"},
                    "sru": {
                        "query": strip_chars(query),
                        "query_es": query_string,
                        "start_record": start_record,
                        "maximum_records": maximum_records,
                    },
                }
            }
            response = self.make_response(pid_fetcher=document_id_fetcher, search_result=result)
            # Add caching headers for search results (short cache with stale-while-revalidate)
            response.headers["Vary"] = "Accept"
            _add_cache_headers(
                response,
                max_age=SEARCH_CACHE_MAX_AGE,
                stale_while_revalidate=SEARCH_STALE_WHILE_REVALIDATE,
            )
            return response

        # Explain operation (default) - cacheable for longer duration
        explain = Explain("api/sru/documents")
        content = str(explain)
        etag = _generate_etag(content)
        # Conditional GET: return 304 if client already has the current version
        # Check If-None-Match header (may contain multiple ETags or wildcard)
        if_none_match = flask_request.headers.get("If-None-Match", "")
        client_etags = [e.strip() for e in if_none_match.split(",")]
        if etag in client_etags or "*" in client_etags:
            not_modified = Response(status=304)
            not_modified.headers["ETag"] = etag
            not_modified.headers["Cache-Control"] = f"public, max-age={EXPLAIN_CACHE_MAX_AGE}"
            not_modified.headers["Vary"] = "Accept"
            raise HTTPException(response=not_modified)
        response = Response(content)
        response.headers["Content-Type"] = "application/xml"
        response.headers["Vary"] = "Accept"
        # Add caching headers for explain (long cache with ETag)
        _add_cache_headers(response, max_age=EXPLAIN_CACHE_MAX_AGE, etag=etag)
        raise HTTPException(response=response)
