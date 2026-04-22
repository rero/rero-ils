# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
# Copyright (C) 2019-2022 UCLouvain
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

"""RERO Document JSON DublinCore serialization."""

from dcxml import simpledc
from flask import current_app, request
from invenio_records_rest.serializers.dc import (
    DublinCoreSerializer as _DublinCoreSerializer,
)
from lxml import etree
from lxml.builder import ElementMaker
from werkzeug.local import LocalProxy

from rero_ils.modules.documents.api import Document
from rero_ils.modules.documents.dojson.contrib.jsontodc import dublincore
from rero_ils.modules.sru.cql_parser import SRU_DC_SCHEMA_URI

from ..dumpers import document_replace_refs_dumper
from ..utils import process_i18n_literal_fields

DEFAULT_LANGUAGE = LocalProxy(lambda: current_app.config.get("BABEL_DEFAULT_LANGUAGE"))


class DublinCoreSerializer(_DublinCoreSerializer):
    """Dublin Core serializer for document records.

    This serializer transforms RERO ILS document records into Dublin Core XML format,
    following the Dublin Core Metadata Element Set specifications. It handles both
    individual record serialization and search result serialization with SRU support.

    The serializer performs the following transformations:
        - Converts RERO ILS JSON documents to Dublin Core XML
        - Resolves record references and processes internationalized fields
        - Handles contribution data with i18n support
        - Generates SRU-compliant search responses

    Note:
        This serializer loads complete records into memory and is not suitable
        for serializing large numbers of records (>1000). For bulk exports,
        consider using streaming serialization.

    See Also:
        - Dublin Core Metadata Initiative: https://dublincore.org/
        - SRU Protocol: https://www.loc.gov/standards/sru/
    """

    # Default namespace mapping.
    namespace = {
        "dc": "http://purl.org/dc/elements/1.1/",
        "xml": "xml",
    }
    # Default container element attributes.
    # TODO: save local dc schema
    container_attribs = {
        "{http://www.w3.org/2001/XMLSchema-instance}schemaLocation": "https://www.loc.gov/standards/sru "
        "https://www.loc.gov/standards/sru/recordSchemas/dc-schema.xsd",
    }
    # Default container element.
    container_element = "record"

    def transform_record(self, pid, record, links_factory=None, language=DEFAULT_LANGUAGE, **kwargs):
        """Transform a document record into Dublin Core intermediate representation.

        This method converts a RERO ILS document record into a Dublin Core
        compatible dictionary format by:
            1. Dumping the record with resolved references
            2. Processing contribution fields with i18n support
            3. Applying Dublin Core transformation rules

        Args:
            pid (str): Persistent identifier of the record.
            record (Document): The document record instance to transform.
            links_factory (callable, optional): Factory function for generating
                record links. Defaults to None.
            language (str, optional): Target language for i18n fields.
                Defaults to application's BABEL_DEFAULT_LANGUAGE.
            **kwargs: Additional keyword arguments passed to the transformation.

        Returns:
            dict: Dublin Core representation of the record with standard DC elements
                (dc:title, dc:creator, dc:date, dc:identifier, etc.).
        """
        record = record.dumps(document_replace_refs_dumper)
        if contributions := record.pop("contribution", []):
            record["contribution"] = process_i18n_literal_fields(contributions)
        return dublincore.do(record, language=language)

    def transform_search_hit(self, pid, record, links_factory=None, language=DEFAULT_LANGUAGE, **kwargs):
        """Transform a search hit into Dublin Core intermediate representation.

        Retrieves the complete document record by PID and delegates to
        :meth:`transform_record` for the actual transformation.

        Args:
            pid (str): Persistent identifier of the document.
            record (dict): search index hit source (minimal record data).
            links_factory (callable, optional): Factory function for generating
                record links. Defaults to None.
            language (str, optional): Target language for i18n fields.
                Defaults to application's BABEL_DEFAULT_LANGUAGE.
            **kwargs: Additional keyword arguments passed to transform_record.

        Returns:
            dict: Dublin Core representation of the record.
        """
        record = Document.get_record_by_pid(pid)
        return self.transform_record(
            pid=pid,
            record=record,
            links_factory=links_factory,
            language=language,
            **kwargs,
        )

    def serialize_search(self, pid_fetcher, search_result, links=None, item_links_factory=None, **kwargs):
        """Serialize search index search results into Dublin Core XML.

        Generates an SRU-compliant searchRetrieveResponse containing Dublin Core
        records for all search hits. The response includes:
            - Total number of matching records
            - Dublin Core XML records for each hit
            - SRU metadata (query echo, pagination info)
            - Next record position for pagination

        The method processes search results in the following order:
            1. Extract SRU metadata and pagination info from search results
            2. Transform each search hit to Dublin Core format
            3. Build XML structure with SRU envelope
            4. Add echoed search parameters for SRU compliance

        Args:
            pid_fetcher (callable): Function to extract persistent identifier from hits.
                Currently unused; PIDs are extracted directly from record source.
            search_result (dict): search index search response containing:
                - hits.total.value: Total number of matching documents
                - hits.hits: List of search result hits
                - hits.sru: SRU-specific metadata (optional)
            links (dict, optional): Additional links to include in response.
                Currently unused. Defaults to None.
            item_links_factory (callable, optional): Factory function for generating
                per-record links. Defaults to None.
            **kwargs: Additional keyword arguments passed to transformation methods.

        Returns:
            bytes: UTF-8 encoded XML string containing the complete SRU response
                with Dublin Core records.

        Note:
            The 'ln' query parameter from the request controls the output language
            for internationalized fields.
        """
        total = search_result["hits"]["total"]["value"]
        sru = search_result["hits"].get("sru", {})
        operation = sru.get("operation")
        start_record = sru.get("start_record", 0)
        maximum_records = sru.get("maximum_records", 0)
        cql_query = sru.get("cql_query")
        search_query = sru.get("search_query")
        record_schema = sru.get("record_schema", SRU_DC_SCHEMA_URI)
        result_set_id = sru.get("result_set_id")
        result_set_ttl = sru.get("result_set_ttl", 0)
        next_record = start_record + maximum_records

        srw_ns = "http://www.loc.gov/zing/srw/"
        element = ElementMaker(namespace=srw_ns, nsmap={"zs": srw_ns})
        xml_root = element.searchRetrieveResponse()
        if sru:
            xml_root.append(element.version("1.1"))
        xml_root.append(element.numberOfRecords(str(total)))
        if result_set_id:
            xml_root.append(element.resultSetId(result_set_id))
            xml_root.append(element.resultSetIdleTime(str(result_set_ttl)))
        xml_records = element.records()

        language = request.args.get("ln", DEFAULT_LANGUAGE)
        for hit in search_result["hits"]["hits"]:
            record = hit["_source"]
            pid = record["pid"]
            record = self.transform_search_hit(
                pid=pid,
                record=record,
                links_factory=item_links_factory,
                language=language,
                **kwargs,
            )
            element_record = simpledc.dump_etree(
                record,
                container=self.container_element,
                nsmap=self.namespace,
                attribs=self.container_attribs,
            )
            xml_records.append(element_record)
        if len(xml_records):
            xml_root.append(xml_records)

        if sru:
            if maximum_records > 0 and next_record <= total:
                xml_root.append(element.nextRecordPosition(str(next_record)))
            echoed_search_rr = element.echoedSearchRetrieveRequest()
            echoed_search_rr.append(element.version("1.1"))
            if operation:
                echoed_search_rr.append(element.operation(operation))
            if cql_query:
                echoed_search_rr.append(element.query(cql_query))
            if search_query:
                echoed_search_rr.append(element.search_query(search_query))
            echoed_search_rr.append(element.startRecord(str(start_record)))
            echoed_search_rr.append(element.maximumRecords(str(maximum_records)))
            echoed_search_rr.append(element.recordPacking("XML"))
            echoed_search_rr.append(element.recordSchema(record_schema))
            echoed_search_rr.append(element.resultSetTTL(str(result_set_ttl)))
            xml_root.append(echoed_search_rr)
        return etree.tostring(xml_root, encoding="utf-8", method="xml", pretty_print=True)
