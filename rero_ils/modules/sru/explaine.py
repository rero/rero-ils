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


"""SRU explaine.

http://www.loc.gov/standards/sru/explain/
"""

import jsonref
from flask import current_app
from invenio_search import current_search
from lxml import etree
from lxml.builder import ElementMaker

from .cql_parser import ES_INDEX_MAPPINGS
from ..utils import get_schema_for_resource


class Explain():
    """SRU explain class."""

    def __init__(self, database, doc_type='doc'):
        """Constructor."""
        self.database = database
        self.number_of_records = current_app.config.get(
            'RERO_SRU_NUMBER_OF_RECORDS', 100)
        self.maximum_records = current_app.config.get(
            'RERO_SRU_MAXIMUM_RECORDS', 1000)
        self.doc_type = doc_type
        self.index = current_app.config.get(
            'RECORDS_REST_ENDPOINTS', {}
        ).get(doc_type, {}).get('search_index')
        self.es_mappings = {}
        for index in self.get_es_mappings(self.index):
            self.es_mappings[index.lower().replace('.', '__')] = index
        self.init_xml()

    def __str__(self):
        """String representation of the object."""
        return etree.tostring(self.xml_root, pretty_print=True).decode()

    def get_properties(self, data):
        """Get properties."""
        keys = []
        for key, value in data.items():
            if isinstance(value, dict):
                properties = value.get('properties')
                if properties:
                    sub_keys = self.get_properties(properties)
                    for sub_key in sub_keys:
                        if '.' in sub_key and sub_key[0] != '$':
                            keys.append('.'.join([key, sub_key]))
                        elif properties[sub_key].get('index', True):
                            keys.append('.'.join([key, sub_key]))
                elif key[0] != '$':
                    keys.append(key)
        return keys

    def get_es_mappings(self, index):
        """Get mappings from ES."""
        mappings = {}
        try:
            index_alias = current_search.aliases.get(index)
            index_file_name = list(index_alias.values())[0]
            data = jsonref.load(open(index_file_name))
            mappings = self.get_properties(
                data.get('mappings').get('properties'))
        except Exception:
            pass
        return mappings

    def init_xml(self):
        """Init XML."""
        sru_ns = 'http://www.loc.gov/standards/sru/'
        element_sru = ElementMaker(
            namespace=sru_ns,
            nsmap={'sru': sru_ns}
        )
        zr_ns = "http://explain.z3950.org/dtd/2.1/"
        element_zr = ElementMaker(
            namespace=zr_ns,
            nsmap={'zr': zr_ns}
        )

        self.xml_root = element_sru.explainResponse()
        self.xml_root.append(element_sru.version('1.1'))
        record = element_sru.record()
        record.append(element_sru.recordPacking('xml'))
        record.append(element_sru.recordSchema(
            'http://explain.z3950.org/dtd/2.1/'))
        record_data = element_sru.recordData()
        explain = element_zr.explain()

        server_info = element_zr.serverInfo({
            'protocol': 'SRU',
            'version': '1.1',
            'transport': current_app.config.get('RERO_ILS_APP_URL_SCHEME'),
            'method': 'GET'
        })
        server_info.append(element_zr.host(
            current_app.config.get('RERO_ILS_APP_HOST')))
        # server_info.append(element_zr.port('5000'))
        server_info.append(element_zr.database(self.database))
        explain.append(server_info)

        index_info = element_zr.indexInfo()
        index_info.append(self.init_index_info_dc())
        index_info.append(self.init_index_info())
        explain.append(index_info)

        schema_info = element_zr.schemaInfo()
        schema_info.append(self.init_schema_info(element_zr))
        explain.append(schema_info)

        config_info = element_zr.schemaInfo()
        config_info.append(self.init_config_info(element_zr))
        explain.append(config_info)

        record_data.append(explain)
        record.append(record_data)
        self.xml_root.append(record)

    def init_index_info_dc(self):
        """Init index info for DC."""
        dc_ns = 'info:srw/cql-context-set/1/dc-v1.1'
        element_dc = ElementMaker(
            namespace=dc_ns,
            nsmap={'dc': dc_ns}
        )
        index = element_dc.index()
        dc_map = element_dc.map()
        for dc_index in ES_INDEX_MAPPINGS:
            dc_map.append(element_dc.name(dc_index.replace('dc.', '')))
        index.append(dc_map)
        return index

    def init_index_info(self):
        """Init index info."""
        rero_ils_ns = get_schema_for_resource('doc')
        element_rero_ils = ElementMaker(
            namespace=rero_ils_ns,
            nsmap={'rero-ils': rero_ils_ns}
        )
        index = element_rero_ils.index()
        es_map = element_rero_ils.map()
        for rero_ils_index in self.es_mappings.keys():
            es_map.append(element_rero_ils.name(rero_ils_index))
        index.append(es_map)
        return index

    def init_schema_info(self, element):
        """Init schema info."""
        schema = element.schemaInfo()
        # Todo: documents -> doc
        schema.append(element.set(
            {
                'name': 'json',
                'identifier': get_schema_for_resource('doc')
                }
        ))
        return schema

    def init_config_info(self, element):
        """Init config info."""
        config = element.configInfo()
        config.append(element.default(
            str(self.number_of_records),
            {'type': 'numberOfRecords'}
        ))
        config.append(element.setting(
            str(self.maximum_records),
            {'type': 'maximumRecords'}
        ))
        return config
