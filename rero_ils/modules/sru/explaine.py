# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2020 RERO
# Copyright (C) 2020 UCLouvain
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

import requests
from flask import current_app
from lxml import etree
from lxml.etree import Element, QName, SubElement

from .cql_parser import ES_INDEX_MAPPINGS
from ..utils import get_schema_for_resource

SRU_NS = 'http://www.loc.gov/standards/sru/'
ZR_NS = "http://explain.z3950.org/dtd/dtd/zeerex-2.0.xsd"


class Explain():
    """SRU explain class."""

    def __init__(self, database, number_of_records=10, maximum_records=100,
                 doc_type='doc'):
        """Constructor."""
        self.database = database
        self.number_of_records = number_of_records
        self.maximum_records = maximum_records
        etree.register_namespace('sru', SRU_NS)
        etree.register_namespace('zr', ZR_NS)
        self.doc_type = doc_type
        self.index = current_app.config.get(
            'RECORDS_REST_ENDPOINTS', {}
        ).get(doc_type, {}).get('search_index')
        self.indexes = self.get_es_mappings(self.index)
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
        hosts = current_app.config.get('SEARCH_ELASTIC_HOSTS')
        url = f'http://{hosts[0]}/{index}/_mappings'
        request = requests.get(url)
        data = next(
            iter(request.json().values())
        ).get('mappings', {}).get('properties')
        return self.get_properties(data)

    def init_xml(self):
        """Init XML."""
        self.xml_root = Element(
            QName(SRU_NS, 'explainResponse'),
            nsmap={'sru': SRU_NS}
        )
        SubElement(self.xml_root, QName(SRU_NS, 'version')).text = '1.1'
        self.xml_record = SubElement(
            self.xml_root,
            QName(SRU_NS, 'record')
        )
        SubElement(
            self.xml_record,
            QName(SRU_NS, 'recordPacking')
        ).text = 'XML'
        SubElement(
            self.xml_record,
            QName(SRU_NS, 'recordSchema')
        ).text = 'http://explain.z3950.org/dtd/2.1/'
        xml_record_data = SubElement(
            self.xml_record,
            QName(SRU_NS, 'recordData')
        )

        xml_record_data = SubElement(
            self.xml_record,
            QName(SRU_NS, 'recordData')
        )
        SubElement(
            xml_record_data,
            QName(ZR_NS, 'explain'),
            nsmap={'zr': ZR_NS}
        )
        self.xml_server_info = SubElement(
            xml_record_data,
            QName(ZR_NS, 'serverInfo')
        )
        SubElement(
            self.xml_server_info,
            QName(ZR_NS, 'explain'),
            attrib={
                'protocol': 'SRU',
                'version': '1.1',
                'transport': current_app.config.get('RERO_ILS_APP_URL_SCHEME'),
                'method': 'GET'
            }
        )
        SubElement(
            self.xml_server_info,
            QName(ZR_NS, 'host')
        ).text = current_app.config.get('RERO_ILS_APP_HOST')
        SubElement(
            self.xml_server_info,
            QName(ZR_NS, 'database')
        ).text = self.database

        self.xml_index_info = SubElement(
            self.xml_server_info,
            QName(ZR_NS, 'indexInfo')
        )
        self.init_index_info_dc()
        self.init_index_info()
        self.init_schema_info()
        self.init_config_info()

    def init_index_info_dc(self):
        """Init index info for DC."""
        SubElement(
            self.xml_index_info,
            QName(ZR_NS, 'set'),
            attrib={
                'name': 'dc',
                'identifier': 'info:srw/cql-context-set/1/dc-v1.1'
            }
        )
        xml_index_info_index = SubElement(
            self.xml_index_info,
            QName(ZR_NS, 'index'),
        )
        xml_index_info_index_map = SubElement(
            xml_index_info_index,
            QName(ZR_NS, 'map'),
        )
        for dc_index in ES_INDEX_MAPPINGS:
            SubElement(
                xml_index_info_index_map,
                QName(ZR_NS, 'name'),
                attrib={
                    'set': 'dc',
                }
            ).text = dc_index.replace('dc.', '')

    def init_index_info(self):
        """Init index info."""
        SubElement(
            self.xml_index_info,
            QName(ZR_NS, 'set'),
            attrib={
                'name': '',
                'identifier': 'info:documents'
            }
        )
        xml_index_info_index = SubElement(
            self.xml_index_info,
            QName(ZR_NS, 'index'),
        )
        xml_index_info_index_map = SubElement(
            xml_index_info_index,
            QName(ZR_NS, 'map'),
        )

        mappings = self.get_es_mappings(self.index)
        for index in mappings:
            SubElement(
                xml_index_info_index_map,
                QName(ZR_NS, 'name'),
                attrib={
                    'set': '',
                }
            ).text = index

    def init_schema_info(self):
        """Init schema info."""
        xml_schema_info = SubElement(
            self.xml_server_info,
            QName(ZR_NS, 'schemaInfo')
        )
        SubElement(
            xml_schema_info,
            QName(ZR_NS, 'set'),
            # Todo: documents -> doc
            attrib={
                'name': 'json',
                'identifier': get_schema_for_resource('doc')
            }
        ).text = str(self.number_of_records)

    def init_config_info(self):
        """Init config info."""
        xml_config_info = SubElement(
            self.xml_server_info,
            QName(ZR_NS, 'configInfo')
        )
        SubElement(
            xml_config_info,
            QName(ZR_NS, 'default'),
            attrib={'type': 'numberOfRecords'}
        ).text = str(self.number_of_records)
        SubElement(
            xml_config_info,
            QName(ZR_NS, 'setting'),
            attrib={'type': 'maximumRecords'}
        ).text = str(self.maximum_records)
