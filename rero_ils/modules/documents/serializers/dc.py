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
from invenio_records_rest.serializers.dc import \
    DublinCoreSerializer as _DublinCoreSerializer
from lxml import etree
from lxml.builder import ElementMaker
from werkzeug.local import LocalProxy

from rero_ils.modules.documents.api import Document
from rero_ils.modules.documents.dojson.contrib.jsontodc import dublincore

from ..dumpers import document_replace_refs_dumper
from ..utils import process_i18n_literal_fields

DEFAULT_LANGUAGE = LocalProxy(
    lambda: current_app.config.get('BABEL_DEFAULT_LANGUAGE'))


class DublinCoreSerializer(_DublinCoreSerializer):
    """Dublin Core serializer for records.

    Note: This serializer is not suitable for serializing large number of
    records.
    """

    # Default namespace mapping.
    namespace = {
        'dc': 'http://purl.org/dc/elements/1.1/',
        'xml': 'xml',
    }
    # Default container element attributes.
    # TODO: save local dc schema
    container_attribs = {
        '{http://www.w3.org/2001/XMLSchema-instance}schemaLocation':
        'https://www.loc.gov/standards/sru '
        'https://www.loc.gov/standards/sru/recordSchemas/dc-schema.xsd',
    }
    # Default container element.
    container_element = 'record'

    def transform_record(self, pid, record, links_factory=None,
                         language=DEFAULT_LANGUAGE, **kwargs):
        """Transform record into an intermediate representation."""
        record = record.dumps(document_replace_refs_dumper)
        if contributions := record.pop('contribution', []):
            record['contribution'] = process_i18n_literal_fields(contributions)
        record = dublincore.do(record, language=language)
        return record

    def transform_search_hit(self, pid, record, links_factory=None,
                             language=DEFAULT_LANGUAGE, **kwargs):
        """Transform search result hit into an intermediate representation."""
        record = Document.get_record_by_pid(pid)
        return self.transform_record(
            pid=pid,
            record=record,
            links_factory=links_factory,
            language=language,
            **kwargs
        )

    def serialize_search(self, pid_fetcher, search_result, links=None,
                         item_links_factory=None, **kwargs):
        """Serialize a search result.

        :param pid_fetcher: Persistent identifier fetcher.
        :param search_result: Elasticsearch search result.
        :param links: Dictionary of links to add to response.
        :param item_links_factory: Factory function for record links.
        """
        total = search_result['hits']['total']['value']
        sru = search_result['hits'].get('sru', {})
        start_record = sru.get('start_record', 0)
        maximum_records = sru.get('maximum_records', 0)
        query = sru.get('query')
        query_es = sru.get('query_es')
        next_record = start_record + maximum_records + 1

        element = ElementMaker()
        xml_root = element.searchRetrieveResponse()
        if sru:
            xml_root.append(element.version('1.1'))
        xml_root.append(element.numberOfRecords(str(total)))
        xml_records = element.records()

        language = request.args.get('ln', DEFAULT_LANGUAGE)
        for hit in search_result['hits']['hits']:
            record = hit['_source']
            pid = record['pid']
            record = self.transform_search_hit(
                pid=pid,
                record=record,
                links_factory=item_links_factory,
                language=language,
                **kwargs
            )
            element_record = simpledc.dump_etree(
                record,
                container=self.container_element,
                nsmap=self.namespace,
                attribs=self.container_attribs
            )
            xml_records.append(element_record)
        xml_root.append(xml_records)

        if sru:
            echoed_search_rr = element.echoedSearchRetrieveRequest()
            if query:
                echoed_search_rr.append(element.query(query))
            if query_es:
                echoed_search_rr.append(element.query_es(query_es))
            if start_record:
                echoed_search_rr.append(element.startRecord(str(start_record)))
            if next_record > 1 and next_record < total:
                echoed_search_rr.append(
                    element.nextRecordPosition(str(next_record)))
            if maximum_records:
                echoed_search_rr.append(element.maximumRecords(
                    str(maximum_records)))
            echoed_search_rr.append(element.recordPacking('XML'))
            xml_root.append(echoed_search_rr)
        return etree.tostring(xml_root, encoding='utf-8', method='xml',
                              pretty_print=True)
