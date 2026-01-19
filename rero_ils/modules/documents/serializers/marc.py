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

"""RERO Document JSON MARCXML serialization."""

import re
from copy import deepcopy

from dojson._compat import iteritems, string_types
from dojson.utils import GroupableOrderedDict
from flask import current_app, request
from lxml import etree
from lxml.builder import ElementMaker
from werkzeug.local import LocalProxy

from rero_ils.modules.documents.dojson.contrib.jsontomarc21 import to_marc21
from rero_ils.modules.documents.dojson.contrib.jsontomarc21.model import (
    replace_contribution_sources,
)
from rero_ils.modules.entities.remote_entities.api import RemoteEntitiesSearch
from rero_ils.modules.serializers import JSONSerializer
from rero_ils.modules.utils import strip_chars

DEFAULT_LANGUAGE = LocalProxy(lambda: current_app.config.get("BABEL_DEFAULT_LANGUAGE"))


class DocumentMARCXMLSerializer(JSONSerializer):
    """DoJSON-based MARCXML serializer for RERO ILS documents.

    This serializer converts RERO ILS JSON document records into MARC 21 XML format
    using DoJSON transformation rules. It handles:
        - Document metadata transformation from JSON to MARC 21
        - Holdings and items serialization (configurable)
        - Entity resolution for contributions (authors, contributors)
        - Multi-language support with configurable agent label ordering
        - Filtering by organisation, library, and location

    The serializer can optionally apply XSLT transformations to the output XML.

    Warning:
        This serializer loads complete records and entity data into memory.
        It is not suitable for serializing large numbers of records (>1000)
        due to high memory consumption. For bulk exports, consider streaming
        approaches or batch processing.

    Attributes:
        dumps_kwargs (dict): Additional arguments for XML serialization.
        schema_class (class): Optional schema class for validation.

    See Also:
        - MARC 21 Format: https://www.loc.gov/marc/bibliographic/
        - DoJSON Documentation: https://dojson.readthedocs.io/
    """

    def __init__(self, xslt_filename=None, schema_class=None):
        """Initialize the MARCXML serializer.

        Args:
            xslt_filename (str, optional): Path to an XSLT stylesheet file for
                post-processing the MARCXML output. If provided, the XSLT will be
                applied to transform the generated MARC 21 XML. Defaults to None.
            schema_class (class, optional): Schema class for validating serialized
                output. Currently not actively used. Defaults to None.

        Note:
            The xslt_filename parameter is currently disabled in the code but
            can be enabled for custom transformations (e.g., MARC21slim2MODS).
        """
        # xslt_filename = resource_filename(
        #     'rero_ils', 'xslts/MARC21slim2MODS3-6.xsl')
        self.dumps_kwargs = {}
        if xslt_filename:
            self.dumps_kwargs = {"xslt_filename": xslt_filename}

        self.schema_class = schema_class
        super().__init__()

    # Needed if we use it for documents serialization !
    # def transform_record(self, pid, record, language,
    #                      links_factory=None, **kwargs):
    #     """Transform record into an intermediate representation."""
    #     return to_marc21.do(record, language=language,
    #                         with_holdings_items=True)
    #

    def transform_search_hit(
        self,
        pid,
        record_hit,
        language=None,
        with_holdings_items=True,
        organisation_pids=None,
        library_pids=None,
        location_pids=None,
        links_factory=None,
        **kwargs,
    ):
        """Transform an Elasticsearch search hit into MARC 21 representation.

        Converts a document record from RERO ILS JSON format to MARC 21 format
        using DoJSON transformation rules. Optionally includes holdings and items
        data, filtered by organisation, library, or location.

        Args:
            pid (str): Persistent identifier of the document.
            record_hit (dict): Elasticsearch hit source containing document data.
            language (str, optional): Target language for language-dependent fields.
                Affects contribution label selection. Defaults to None.
            with_holdings_items (bool, optional): Whether to include holdings and
                items in the MARC output. Defaults to True.
            organisation_pids (list, optional): Filter holdings/items by organisation
                PIDs. Only data from these organisations will be included.
                Defaults to None (no filtering).
            library_pids (list, optional): Filter holdings/items by library PIDs.
                Only data from these libraries will be included.
                Defaults to None (no filtering).
            location_pids (list, optional): Filter holdings/items by location PIDs.
                Only data from these locations will be included.
                Defaults to None (no filtering).
            links_factory (callable, optional): Factory for generating record links.
                Currently unused. Defaults to None.
            **kwargs: Additional keyword arguments passed to transformation.

        Returns:
            GroupableOrderedDict: MARC 21 record representation with fields
                organized by tag (e.g., '245__', '100__', '852__').
        """
        return to_marc21.do(
            record_hit,
            language=language,
            with_holdings_items=with_holdings_items,
            organisation_pids=organisation_pids,
            library_pids=library_pids,
            location_pids=location_pids,
        )

    # Needed if we use it for documents serialization !
    # def serialize(self, pid, record, links_factory=None):
    #     """Serialize a single record and persistent identifier.
    #
    #     :param pid: The :class:`invenio_pidstore.models.PersistentIdentifier`
    #         instance.
    #     :param record: The :class:`invenio_records.api.Record` instance.
    #     :param links_factory: Factory function for the link generation,
    #         which are added to the response.
    #     :returns: The object serialized.
    #     """
    #     language = request.args.get('ln', DEFAULT_LANGUAGE)
    #     return dumps(
    #         self.transform_record(pid, record, language, links_factory),
    #         **self.dumps_kwargs
    #     )

    def transform_records(
        self,
        hits,
        pid_fetcher,
        language,
        with_holdings_items=True,
        organisation_pids=None,
        library_pids=None,
        location_pids=None,
        item_links_factory=None,
    ):
        """Transform multiple Elasticsearch hits into MARC 21 records with entity resolution.

        This method processes multiple search hits efficiently by:
            1. Collecting all contribution entity PIDs from all hits
            2. Batch-fetching all entities in a single Elasticsearch query
            3. Enriching each contribution with full entity data
            4. Applying language-specific source ordering for agent labels
            5. Transforming each record to MARC 21 format

        This approach significantly improves performance compared to fetching
        entities individually for each record.

        Args:
            hits (list): List of Elasticsearch search hits, each containing
                a '_source' field with document data.
            pid_fetcher (callable): Function to extract PID from document ID.
            language (str): Target language for entity label selection. Used to
                determine the preferred source order for agent labels.
            with_holdings_items (bool, optional): Include holdings/items data
                in MARC output. Defaults to True.
            organisation_pids (list, optional): Filter by organisation PIDs.
                Defaults to None.
            library_pids (list, optional): Filter by library PIDs. Defaults to None.
            location_pids (list, optional): Filter by location PIDs. Defaults to None.
            item_links_factory (callable, optional): Factory for item links.
                Currently unused. Defaults to None.

        Returns:
            list: List of GroupableOrderedDict objects, each representing a
                MARC 21 record with enriched contribution data.

        Note:
            Entity resolution respects the RERO_ILS_AGENTS_LABEL_ORDER configuration,
            which defines the preferred order of sources (e.g., idref, gnd, rero)
            for different languages.
        """
        # Collect all contribution entity PIDs from all hits for batch resolution.
        # This prevents N+1 query problem by fetching all entities in one ES query.
        contribution_pids = []
        for hit in hits:
            for contribution in hit["_source"].get("contribution", []):
                if contribution_pid := contribution.get("entity", {}).get("pid"):
                    contribution_pids.append(contribution_pid)
        # Batch-fetch all unique entities from Elasticsearch and cache them
        # in a dictionary for O(1) lookup during record processing.
        search = RemoteEntitiesSearch().filter("terms", pid=list(set(contribution_pids)))
        es_contributions = {}
        for hit in search.scan():
            contribution = hit.to_dict()
            es_contributions[contribution["pid"]] = contribution

        # Get language-specific source order for agent labels (e.g., prefer idref
        # for French, gnd for German). Falls back to default language if not found.
        order = current_app.config.get("RERO_ILS_AGENTS_LABEL_ORDER", {})
        fallback_key = order.get("fallback")
        fallback_order = order.get(fallback_key, []) if fallback_key else []
        source_order = order.get(language, fallback_order)
        records = []
        for hit in hits:
            document = hit["_source"]
            # Enrich each contribution with full entity data from cache and apply
            # language-specific source ordering for authorized access points.
            contributions = document.get("contribution", [])
            for contribution in contributions:
                contribution_pid = contribution.get("entity", {}).get("pid")
                if contribution_pid in es_contributions:
                    # Deep copy prevents modifying the cached entity data
                    contribution["entity"] = deepcopy(es_contributions[contribution_pid])
                    # Select the best authorized access point based on language preferences
                    replace_contribution_sources(contribution=contribution, source_order=source_order)

            # Transform the enriched document to MARC 21 format with all filters applied
            record = self.transform_search_hit(
                pid=pid_fetcher(hit["_id"], document),
                record_hit=document,
                language=language,
                with_holdings_items=with_holdings_items,
                organisation_pids=organisation_pids,
                library_pids=library_pids,
                location_pids=location_pids,
                links_factory=item_links_factory,
            )
            records.append(record)
        return records

    # Needed if we use it for documents serialization !
    # def serialize_search(self, pid_fetcher, search_result,
    #                      item_links_factory=None, **kwargs):
    #     """Serialize a search result.
    #
    #     :param pid_fetcher: Persistent identifier fetcher.
    #     :param search_result: Elasticsearch search result.
    #     :param item_links_factory: Factory function for the items in result.
    #         (Default: ``None``)
    #     :returns: The objects serialized.
    #     """
    #     language = request.args.get('ln', DEFAULT_LANGUAGE)
    #     records = self.transform_records(
    #         hits=search_result['hits']['hits'],
    #         pid_fetcher=pid_fetcher,
    #         language=language,
    #         item_links_factory=item_links_factory
    #     )
    #     return dumps(records, **self.dumps_kwargs)


class DocumentMARCXMLSRUSerializer(DocumentMARCXMLSerializer):
    """DoJSON-based MARCXML serializer with SRU protocol support.

    This serializer extends :class:`DocumentMARCXMLSerializer` to generate
    MARC 21 XML wrapped in an SRU (Search/Retrieve via URL) envelope. It is
    designed specifically for SRU Z39.50 protocol compliance.

    The serializer produces searchRetrieveResponse XML documents containing:
        - SRU version and metadata
        - Number of records and pagination info
        - MARC 21 XML records with proper namespace declarations
        - Echoed search request parameters
        - Result set TTL and schema information

    XML Structure:
        The output follows the MARC 21 XML Schema with SRU envelope:
            <zs:searchRetrieveResponse xmlns:zs="http://www.loc.gov/zing/srw/">
                <zs:version>1.1</zs:version>
                <zs:numberOfRecords>...</zs:numberOfRecords>
                <zs:records>
                    <zs:record>
                        <zs:recordData>
                            <record xmlns="http://www.loc.gov/MARC21/slim">...</record>
                        </zs:recordData>
                    </zs:record>
                </zs:records>
                <zs:echoedSearchRetrieveRequest>...</zs:echoedSearchRetrieveRequest>
            </zs:searchRetrieveResponse>

    Warning:
        Like its parent class, this serializer is memory-intensive and not
        suitable for large result sets (>1000 records).

    Attributes:
        MARC21_ZS (str): SRU/ZS namespace URI.
        MARC21_REC (str): MARC 21 XML Schema namespace URI.

    See Also:
        - SRU Protocol: https://www.loc.gov/standards/sru/
        - MARC 21 XML: https://www.loc.gov/standards/marcxml/
    """

    MARC21_ZS = "http://www.loc.gov/zing/srw/"
    MARC21_REC = "http://www.loc.gov/MARC21/slim"
    """MARCXML XML Schema"""

    def dumps_etree(self, total, records, sru, xslt_filename=None, prefix=None):
        """Serialize MARC records into an SRU XML ElementTree.

        Constructs a complete SRU searchRetrieveResponse XML tree containing
        MARC 21 records with proper namespace declarations and metadata.

        Args:
            total (dict): Total hits information from Elasticsearch with 'value' key.
            records (list or dict): Either a list of MARC records (for search results)
                or a single MARC record dict. Each record should be a GroupableOrderedDict
                with MARC fields as keys (e.g., 'leader', '245__', '100__').
            sru (dict): SRU request parameters containing:
                - start_record (int): Starting position in result set
                - maximum_records (int): Number of records requested
                - query (str): Original CQL query string
                - query_es (str): Elasticsearch query translation
            xslt_filename (str, optional): Path to XSLT stylesheet for transformation.
                Currently disabled but can be used for output formatting. Defaults to None.
            prefix (str, optional): XML namespace prefix for MARC fields.
                If None, no prefix is used. Defaults to None.

        Returns:
            lxml.etree.Element: Root element of the SRU response tree. For a single
                record, returns just the record element. For search results, returns
                the complete searchRetrieveResponse element.

        Note:
            The method handles both single record and multiple records differently:
                - Single record: Returns minimal record wrapper
                - Multiple records: Returns full SRU searchRetrieveResponse
        """
        _ = xslt_filename  # intentionally unused; kept for API compatibility
        element = ElementMaker(namespace=self.MARC21_ZS, nsmap={"zs": self.MARC21_ZS})

        def dump_record(record, idx):
            """Serialize a single MARC record to SRU XML format.

            Converts a MARC record dictionary into an XML structure with:
                - Control fields (001-009): Simple tag with content
                - Data fields (010-999): Tag with indicators and subfields
                - Leader field: Special header field

            Args:
                record (GroupableOrderedDict): MARC record with fields as keys.
                idx (int): Record position in the result set (1-based).

            Returns:
                lxml.etree.Element: SRU record element containing the MARC data.
            """
            rec_element = ElementMaker(namespace=self.MARC21_REC, nsmap={prefix: self.MARC21_REC})
            data_element = ElementMaker(namespace=self.MARC21_REC, nsmap={prefix: self.MARC21_REC})
            rec = element.record()
            rec.append(element.recordPacking("xml"))
            rec.append(element.recordSchema("marcxml"))

            rec_record_data = element.recordData()
            rec_data = rec_element.record()

            if leader := record.get("leader"):
                rec_data.append(data_element.leader(leader))

            if isinstance(record, GroupableOrderedDict):
                items = record.iteritems(with_order=False, repeated=True)
            else:
                items = iteritems(record)

            # Process each MARC field (control fields and data fields)
            for df, subfields in items:
                # Control fields (001-009): Simple fields with just a tag and text content
                if len(df) == 3:
                    if isinstance(subfields, string_types):
                        controlfield = data_element.controlfield(subfields)
                        controlfield.attrib["tag"] = df[:3]
                        rec_data.append(controlfield)
                    elif isinstance(subfields, (list, tuple, set)):
                        for subfield in subfields:
                            controlfield = data_element.controlfield(subfield)
                            controlfield.attrib["tag"] = df[:3]
                            rec_data.append(controlfield)
                else:
                    # Data fields (010-999): Complex fields with indicators and subfields
                    # Skip leader as it's already processed above
                    if df == "leader":
                        continue

                    # Ensure subfields is iterable
                    if not isinstance(subfields, (list, tuple, set)):
                        subfields = (subfields,)

                    # Convert underscores to spaces for indicators (e.g., '245_0' -> '245 0')
                    df = df.replace("_", " ")
                    for subfield in subfields:
                        if not isinstance(subfield, (list, tuple, set)):
                            subfield = [subfield]

                        for s in subfield:
                            datafield = data_element.datafield()
                            datafield.attrib["tag"] = df[:3]
                            datafield.attrib["ind1"] = df[3]
                            datafield.attrib["ind2"] = df[4]

                            if isinstance(s, GroupableOrderedDict):
                                items = s.iteritems(with_order=False, repeated=True)
                            elif isinstance(s, dict):
                                items = iteritems(s)
                            else:
                                datafield.append(data_element.subfield(s))

                                items = ()

                            for code, value in items:
                                if isinstance(value, string_types):
                                    datafield.append(data_element.subfield(strip_chars(value), code=code))
                                else:
                                    for v in value:
                                        datafield.append(data_element.subfield(strip_chars(v), code=code))
                            rec_data.append(datafield)
            rec_record_data.append(rec_data)
            rec.append(rec_record_data)
            rec.append(element.recordPosition(str(idx)))
            return rec

        if isinstance(records, dict):
            root = dump_record(records, 1)
        else:
            number_of_records = total["value"]
            start_record = sru.get("start_record", 1)
            maximum_records = sru.get("maximum_records", 0)
            query = sru.get("query")
            query_es = sru.get("query_es")
            next_record = start_record + maximum_records
            root = element.searchRetrieveResponse()
            root.append(element.version("1.1"))
            root.append(element.numberOfRecords(str(number_of_records)))
            if next_record > 1 and next_record <= number_of_records:
                root.append(element.nextRecordPosition(str(next_record)))
            data = element.records()
            for idx, record in enumerate(records, start_record):
                data.append(dump_record(record, idx))
            root.append(data)
            echoed_search_rr = element.echoedSearchRetrieveRequest()
            echoed_search_rr.append(element.version("1.1"))
            if query:
                echoed_search_rr.append(element.query(query))
            if query_es:
                echoed_search_rr.append(element.query_es(query_es))
            if start_record:
                echoed_search_rr.append(element.startRecord(str(start_record)))
            if maximum_records:
                echoed_search_rr.append(element.maximumRecords(str(maximum_records)))
            echoed_search_rr.append(element.recordPacking("XML"))
            echoed_search_rr.append(element.recordSchema("info:sru/schema/1/marcxml-v1.1-light"))
            echoed_search_rr.append(element.resultSetTTL("0"))
            root.append(echoed_search_rr)

        # Needed if we use display with XSLT file.
        # if xslt_filename is not None:
        #     xslt_root = etree.parse(open(xslt_filename))
        #     transform = etree.XSLT(xslt_root)
        #     root = transform(root).getroot()

        return root

    def dumps(self, total, records, sru, xslt_filename=None, **kwargs):
        """Dump records into a MarcXMLSRU file."""
        root = self.dumps_etree(total=total, records=records, sru=sru, xslt_filename=xslt_filename)
        return etree.tostring(root, pretty_print=True, xml_declaration=True, encoding="UTF-8", **kwargs)

    def serialize_search(self, pid_fetcher, search_result, item_links_factory=None, **kwargs):
        """Serialize Elasticsearch search results into SRU MARCXML format.

        This method orchestrates the complete serialization process:
            1. Extracts language and filtering parameters from request
            2. Parses organisation/library/location filters from query
            3. Transforms all records with entity resolution
            4. Wraps results in SRU searchRetrieveResponse envelope

        The method supports the following request parameters:
            - ln: Language code for i18n fields
            - without_items: Flag to exclude holdings/items (default: False)

        Organisation/library/location filters are automatically extracted from
        the Elasticsearch query string when present.

        Args:
            pid_fetcher (callable): Function to extract PID from document ID.
            search_result (dict): Elasticsearch search response with structure:
                - hits.total: Total number of matching documents
                - hits.hits: Array of search result hits
                - hits.sru: SRU-specific metadata (query, pagination)
            item_links_factory (callable, optional): Factory for item links.
                Currently unused. Defaults to None.
            **kwargs: Additional arguments passed to dumps() method.

        Returns:
            bytes: UTF-8 encoded XML string containing the complete SRU response
                with MARC 21 records, including XML declaration.

        Example::

            serializer = DocumentMARCXMLSRUSerializer()
            xml = serializer.serialize_search(
                pid_fetcher=lambda id, doc: doc['pid'],
                search_result=es_response
            )
        """
        # Extract request parameters for language and item inclusion
        language = request.args.get("ln", DEFAULT_LANGUAGE)
        without_items_param = request.args.get("without_items", "").lower()
        with_holdings_items = without_items_param not in ("true", "1", "yes")

        # Parse organisation/library/location filters from the Elasticsearch query.
        # These filters control which holdings/items are included in the output.
        sru = search_result["hits"].get("sru", {})
        query_es = sru.get("query_es", "")
        organisation_pids = re.findall(r"organisation_pid:([A-Za-z0-9_-]+)", query_es)
        library_pids = re.findall(r"library_pid:([A-Za-z0-9_-]+)", query_es)
        location_pids = re.findall(r"holdings\.location\.pid:([A-Za-z0-9_-]+)", query_es)
        records = self.transform_records(
            hits=search_result["hits"]["hits"],
            pid_fetcher=pid_fetcher,
            language=language,
            with_holdings_items=with_holdings_items,
            organisation_pids=organisation_pids,
            library_pids=library_pids,
            location_pids=location_pids,
            item_links_factory=item_links_factory,
        )
        return self.dumps(
            total=search_result["hits"]["total"],
            sru=sru,
            records=records,
            **self.dumps_kwargs,
        )
