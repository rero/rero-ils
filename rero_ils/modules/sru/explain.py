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

from weakref import WeakKeyDictionary

import jsonref
from flask import current_app
from invenio_search import current_search
from lxml import etree
from lxml.builder import ElementMaker

from ..utils import get_schema_for_resource
from .cql_parser import SEARCH_INDEX_MAPPINGS, SRU_DC_SCHEMA_URI, SRU_MARCXML_SCHEMA_URI

#: Per-app ES mapping cache. Keyed by Flask app instance so each app gets its
#: own cache and entries are collected when the app is destroyed.
_es_mappings_cache: WeakKeyDictionary = WeakKeyDictionary()


def _get_properties(data):
    """Recursively extract searchable field paths from search mapping properties."""
    keys = []
    for key, value in data.items():
        if not isinstance(value, dict):
            continue
        if properties := value.get("properties"):
            for sub_key in _get_properties(properties):
                first_segment = sub_key.split(".")[0]
                is_compound = "." in sub_key and sub_key[0] != "$"
                first_is_indexed = properties.get(first_segment, {}).get("index", True)
                if is_compound or first_is_indexed:
                    keys.append(f"{key}.{sub_key}")
        elif key[0] != "$" and value.get("index", True):
            keys.append(key)
    return keys


def _get_search_mappings(index):
    """Load and cache field mappings from the Elasticsearch index definition.

    Results are cached per Flask application instance so the cache is isolated
    between apps (e.g. in tests) and is collected when the app is destroyed.

    :param index: The Elasticsearch index alias name.
    :returns: Mapping of normalized index names to ES field paths.
    """
    app = current_app._get_current_object()
    app_cache = _es_mappings_cache.setdefault(app, {})
    if index in app_cache:
        return app_cache[index]
    result = {}
    try:
        index_alias = current_search.aliases.get(index)
        index_file_name = next(iter(index_alias.values()))
        with open(index_file_name, encoding="utf-8") as f:
            data = jsonref.load(f)
        if properties := data.get("mappings", {}).get("properties", {}):
            result = {field.lower().replace(".", "__"): field for field in _get_properties(properties)}
    except Exception:
        current_app.logger.debug("Failed to load Search mappings for index: %s", index, exc_info=True)
    app_cache[index] = result
    return result


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

        :param database: The SRU database path used in the serverInfo element.
        :param doc_type: Document type key for looking up the Elasticsearch index
            in RECORDS_REST_ENDPOINTS configuration. Defaults to ``'doc'``.
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

        :returns: Pretty-printed XML string representation of the Explain response.
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
                - serverInfo (protocol, host, database, authentication)
                - databaseInfo (title, contact, implementation)
                - indexInfo (set declarations + DC indexes + search field indexes)
                - schemaInfo (supported retrieval schemas)
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
                "transport": current_app.config.get("RERO_ILS_URL_SCHEME", "https"),
                "method": "GET",
            }
        )
        server_info.append(element_zr.host(current_app.config.get("RERO_ILS_HOST", "localhost")))
        server_info.append(element_zr.database(self.database))
        server_info.append(element_zr.authentication({"type": "open"}))
        explain.append(server_info)

        explain.append(self.init_database_info(element_zr))

        rero_ils_ns = get_schema_for_resource("doc")
        index_info = element_zr.indexInfo()
        index_info.append(element_zr.set({"identifier": "info:srw/cql-context-set/1/dc-v1.1", "name": "dc"}))
        index_info.append(element_zr.set({"identifier": rero_ils_ns, "name": "rero-ils"}))
        index_info.append(self.init_index_info_dc())
        index_info.append(self.init_index_info())
        explain.append(index_info)

        explain.append(self.init_schema_info(element_zr))
        explain.append(self.init_config_info(element_zr))

        record_data.append(explain)
        record.append(record_data)
        self.xml_root.append(record)

    def init_database_info(self, element):
        """Create the database information element.

        Includes a human-readable title, contact address, and implementation
        block so SRU clients can identify the server software.

        :param element: The ElementMaker instance for creating XML elements.
        :returns: A ``databaseInfo`` lxml Element.
        """
        db_info = element.databaseInfo()
        title = current_app.config.get("RERO_ILS_SRU_DATABASE_TITLE", "RERO ILS Document Search")
        db_info.append(element.title(title, {"lang": "en", "primary": "true"}))
        if contact := current_app.config.get("RERO_ILS_SRU_CONTACT", ""):
            db_info.append(element.contact(contact))
        impl = element.implementation({"version": "1.0", "identifier": "https://github.com/rero/rero-ils"})
        impl.append(element.title("RERO ILS"))
        db_info.append(impl)
        return db_info

    def init_index_info_dc(self):
        """Create the Dublin Core index information element.

        Generates an XML element listing all supported Dublin Core indexes
        from the SEARCH_INDEX_MAPPINGS configuration.

        :returns: lxml Element containing the DC index map with all supported
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

        :returns: lxml Element containing the index map with all search field paths
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
        """Create the schema information element listing supported retrieval schemas.

        :param element: The ElementMaker instance for creating XML elements.
        :returns: A ``schemaInfo`` lxml Element with one ``schema`` child per
            supported retrieval schema.
        """
        schema_info = element.schemaInfo()
        schema_info.append(
            element.schema({"identifier": SRU_MARCXML_SCHEMA_URI, "name": "marcxml", "retrieve": "true"})
        )
        schema_info.append(element.schema({"identifier": SRU_DC_SCHEMA_URI, "name": "dc", "retrieve": "true"}))
        return schema_info

    def init_config_info(self, element):
        """Create the configuration information element.

        Includes the default and maximum number of records settings
        that control pagination behavior for search results.

        :param element: The ElementMaker instance for creating XML elements.
        :returns: lxml Element containing the default and maximum
            numberOfRecords settings.
        """
        config = element.configInfo()
        config.append(element.default(str(self.number_of_records), {"type": "numberOfRecords"}))
        config.append(element.setting(str(self.maximum_records), {"type": "maximumRecords"}))
        return config
