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


"""SRU Explain response generator.

This module implements the SRU Explain operation as defined in the
SRU (Search/Retrieve via URL) standard.

The Explain operation provides information about the server's capabilities,
supported indexes, schemas, and configuration settings.

See Also:
    - SRU Explain specification: http://www.loc.gov/standards/sru/explain/
    - Z39.50 Explain DTD 2.1: http://explain.z3950.org/dtd/2.1/
"""

from functools import cache

import jsonref
from flask import current_app
from invenio_search import current_search
from lxml import etree
from lxml.builder import ElementMaker

from ..utils import get_schema_for_resource
from .cql_parser import SEARCH_INDEX_MAPPINGS


def _get_properties(data):
    """Recursively extract searchable field paths from search mapping properties."""
    keys = []
    for key, value in data.items():
        if isinstance(value, dict):
            if properties := value.get("properties"):
                sub_keys = _get_properties(properties)
                for sub_key in sub_keys:
                    first_segment = sub_key.split(".")[0]
                    if ("." in sub_key and sub_key[0] != "$") or properties.get(first_segment, {}).get("index", True):
                        keys.append(".".join([key, sub_key]))
            elif key[0] != "$" and value.get("index", True):
                keys.append(key)
    return keys


@cache
def _get_search_mappings(index):
    """Load and cache field mappings from the search index definition.

    :param index: The search index alias name.
    :type index: str
    :returns: Mapping of normalized index names to search field paths.
    :rtype: dict
    """
    try:
        index_alias = current_search.aliases.get(index)
        index_file_name = next(iter(index_alias.values()))
        with open(index_file_name, encoding="utf-8") as f:
            data = jsonref.load(f)
        if properties := data.get("mappings", {}).get("properties", {}):
            return {field.lower().replace(".", "__"): field for field in _get_properties(properties)}
    except Exception:
        current_app.logger.debug("Failed to load search mappings for index: %s", index, exc_info=True)
    return {}


class Explain:
    """SRU Explain response generator.

    Generates an XML Explain response conforming to the Z39.50 Explain DTD 2.1.
    The response includes server information, supported indexes (both Dublin Core
    and RERO-ILS specific), schema information, and configuration settings.

    Attributes:
        database: The SRU database path (e.g., 'api/sru/documents').
        number_of_records: Default number of records returned per request.
        maximum_records: Maximum allowed records per request.
        doc_type: The document type for search index lookup.
        index: The search index name.
        search_mappings: Dictionary mapping normalized index names to search field paths.
        xml_root: The root XML element of the Explain response.

    Example::

        explain = Explain('api/sru/documents')
        print(str(explain))  # Returns XML string
    """

    def __init__(self, database, doc_type="doc"):
        """Initialize the Explain response generator.

        Args:
            database: The SRU database path used in the serverInfo element.
            doc_type: Document type key for looking up the search index
                in RECORDS_REST_ENDPOINTS configuration. Defaults to 'doc'.
        """
        self.database = database
        self.number_of_records = current_app.config.get("RERO_ILS_SRU_NUMBER_OF_RECORDS", 100)
        self.maximum_records = current_app.config.get("RERO_ILS_SRU_MAXIMUM_RECORDS", 1000)
        self.doc_type = doc_type
        self.index = current_app.config.get("RECORDS_REST_ENDPOINTS", {}).get(doc_type, {}).get("search_index")
        self.search_mappings = _get_search_mappings(self.index) if self.index else {}
        self.init_xml()

    def __str__(self):
        """Return the Explain response as a formatted XML string.

        Returns:
            A pretty-printed XML string representation of the Explain response.
        """
        return etree.tostring(self.xml_root, pretty_print=True).decode()

    def init_xml(self):
        """Initialize the XML structure for the Explain response.

        Builds the complete XML document with the following structure:
        - explainResponse (root)
          - version
          - record
            - recordPacking
            - recordSchema
            - recordData
              - explain
                - serverInfo (protocol, host, database)
                - indexInfo (DC indexes + search field indexes)
                - schemaInfo (JSON schema reference)
                - configInfo (default/maximum records settings)
        """
        sru_ns = "http://www.loc.gov/standards/sru/"
        element_sru = ElementMaker(namespace=sru_ns, nsmap={"sru": sru_ns})
        zr_ns = "http://explain.z3950.org/dtd/2.1/"
        element_zr = ElementMaker(namespace=zr_ns, nsmap={"zr": zr_ns})

        self.xml_root = element_sru.explainResponse()
        self.xml_root.append(element_sru.version("1.1"))
        record = element_sru.record()
        record.append(element_sru.recordPacking("xml"))
        record.append(element_sru.recordSchema("http://explain.z3950.org/dtd/2.1/"))
        record_data = element_sru.recordData()
        explain = element_zr.explain()

        server_info = element_zr.serverInfo(
            {
                "protocol": "SRU",
                "version": "1.1",
                "transport": current_app.config.get("RERO_ILS_URL_SCHEME"),
                "method": "GET",
            }
        )
        server_info.append(element_zr.host(current_app.config.get("RERO_ILS_HOST")))
        # server_info.append(element_zr.port('5000'))
        server_info.append(element_zr.database(self.database))
        explain.append(server_info)

        index_info = element_zr.indexInfo()
        index_info.append(self.init_index_info_dc())
        index_info.append(self.init_index_info())
        explain.append(index_info)

        explain.append(self.init_schema_info(element_zr))
        explain.append(self.init_config_info(element_zr))

        record_data.append(explain)
        record.append(record_data)
        self.xml_root.append(record)

    def init_index_info_dc(self):
        """Create the Dublin Core index information element.

        Generates an XML element listing all supported Dublin Core indexes
        from the SEARCH_INDEX_MAPPINGS configuration.

        Returns:
            An lxml Element containing the DC index map with all supported
            Dublin Core search indexes (title, creator, subject, etc.).
        """
        dc_ns = "info:srw/cql-context-set/1/dc-v1.1"
        element_dc = ElementMaker(namespace=dc_ns, nsmap={"dc": dc_ns})
        index = element_dc.index()
        dc_map = element_dc.map()
        for dc_index in SEARCH_INDEX_MAPPINGS:
            dc_map.append(element_dc.name(dc_index.replace("dc.", "")))
        index.append(dc_map)
        return index

    def init_index_info(self):
        """Create the RERO-ILS specific index information element.

        Generates an XML element listing all search index field indexes
        available for searching, using the RERO-ILS namespace.

        Returns:
            An lxml Element containing the index map with all search field paths
            that can be used directly in CQL queries.
        """
        rero_ils_ns = get_schema_for_resource("doc")
        element_rero_ils = ElementMaker(namespace=rero_ils_ns, nsmap={"rero-ils": rero_ils_ns})
        index = element_rero_ils.index()
        search_map = element_rero_ils.map()
        for rero_ils_index in self.search_mappings:
            search_map.append(element_rero_ils.name(rero_ils_index))
        index.append(search_map)
        return index

    def init_schema_info(self, element):
        """Create the schema information element.

        Args:
            element: The ElementMaker instance for creating XML elements.

        Returns:
            An lxml Element containing schema information with the JSON
            schema identifier for the document resource.
        """
        schema = element.schemaInfo()
        schema.append(element.set({"name": "json", "identifier": get_schema_for_resource("doc")}))
        return schema

    def init_config_info(self, element):
        """Create the configuration information element.

        Includes the default and maximum number of records settings
        that control pagination behavior for search results.

        Args:
            element: The ElementMaker instance for creating XML elements.

        Returns:
            An lxml Element containing:
            - default numberOfRecords setting
            - maximum numberOfRecords setting
        """
        config = element.configInfo()
        config.append(element.default(str(self.number_of_records), {"type": "numberOfRecords"}))
        config.append(element.setting(str(self.maximum_records), {"type": "maximumRecords"}))
        return config
