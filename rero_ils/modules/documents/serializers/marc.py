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
from rero_ils.modules.documents.dojson.contrib.jsontomarc21.model import \
    replace_contribution_sources
from rero_ils.modules.entities.remote_entities.api import RemoteEntitiesSearch
from rero_ils.modules.serializers import JSONSerializer
from rero_ils.modules.utils import strip_chars

DEFAULT_LANGUAGE = LocalProxy(
    lambda: current_app.config.get('BABEL_DEFAULT_LANGUAGE'))


class DocumentMARCXMLSerializer(JSONSerializer):
    """DoJSON based MARCXML serializer for documents.

    Note: This serializer is not suitable for serializing large number of
    records due to high memory usage.
    """

    def __init__(self, xslt_filename=None, schema_class=None):
        """Initialize serializer.

        :param dojson_model: The DoJSON model able to convert JSON through the
            ``do()`` function.
        :param xslt_filename: XSLT filename. (Default: ``None``)
        :param schema_class: The schema class. (Default: ``None``)
        """
        # xslt_filename = resource_filename(
        #     'rero_ils', 'xslts/MARC21slim2MODS3-6.xsl')
        self.dumps_kwargs = {}
        if xslt_filename:
            self.dumps_kwargs = dict(xslt_filename=xslt_filename)

        self.schema_class = schema_class
        super().__init__()

    # Needed if we use it for documents serialization !
    # def transform_record(self, pid, record, language,
    #                      links_factory=None, **kwargs):
    #     """Transform record into an intermediate representation."""
    #     return to_marc21.do(record, language=language,
    #                         with_holdings_items=True)
    #

    def transform_search_hit(self, pid, record_hit, language=None,
                             with_holdings_items=True, organisation_pids=None,
                             library_pids=None, location_pids=None,
                             links_factory=None, **kwargs):
        """Transform search result hit into an intermediate representation."""
        return to_marc21.do(
            record_hit,
            language=language,
            with_holdings_items=with_holdings_items,
            organisation_pids=organisation_pids,
            library_pids=library_pids,
            location_pids=location_pids
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

    def transform_records(self, hits, pid_fetcher, language,
                          with_holdings_items=True, organisation_pids=None,
                          library_pids=None, location_pids=None,
                          item_links_factory=None):
        """Transform records into an intermediate representation."""
        # get all linked contributions
        contribution_pids = []
        for hit in hits:
            for contribution in hit['_source'].get('contribution', []):
                contribution_pid = contribution.get('entity', {}).get('pid')
                if contribution_pid:
                    contribution_pids.append(contribution_pid)
        search = RemoteEntitiesSearch() \
            .filter('terms', pid=list(set(contribution_pids)))
        es_contributions = {}
        for hit in search.scan():
            contribution = hit.to_dict()
            es_contributions[contribution['pid']] = contribution

        order = current_app.config.get('RERO_ILS_AGENTS_LABEL_ORDER', {})
        source_order = order.get(language, order.get(order['fallback'], []))
        records = []
        for hit in hits:
            document = hit['_source']
            contributions = document.get('contribution', [])
            for contribution in contributions:
                contribution_pid = contribution.get('entity', {}).get('pid')
                if contribution_pid in es_contributions:
                    contribution['entity'] = deepcopy(
                        es_contributions[contribution_pid])
                    replace_contribution_sources(
                        contribution=contribution,
                        source_order=source_order
                    )

            record = self.transform_search_hit(
                pid=pid_fetcher(hit['_id'], document),
                record_hit=document,
                language=language,
                with_holdings_items=with_holdings_items,
                organisation_pids=organisation_pids,
                library_pids=library_pids,
                location_pids=location_pids,
                links_factory=item_links_factory
            )
            # complete the contributions from refs

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
    """DoJSON based MARCXML SRU serializer for documents.

    Note: This serializer is not suitable for serializing large number of
    records due to high memory usage.
    """

    MARC21_ZS = "http://www.loc.gov/zing/srw/"
    MARC21_REC = "http://www.loc.gov/MARC21/slim"
    """MARCXML XML Schema"""

    def dumps_etree(self, total, records, sru, xslt_filename=None,
                    prefix=None):
        """Dump records into a etree."""
        element = ElementMaker(
            namespace=self.MARC21_ZS,
            nsmap={'zs': self.MARC21_ZS}
        )

        def dump_record(record, idx):
            """Dump a single record."""
            rec_element = ElementMaker(
                namespace=self.MARC21_REC,
                nsmap={prefix: self.MARC21_REC}
            )
            data_element = ElementMaker()
            rec = element.record()
            rec.append(element.recordPacking('xml'))
            rec.append(element.recordSchema('marcxml'))

            rec_record_data = element.recordData()
            rec_data = rec_element.record()

            if leader := record.get('leader'):
                rec_data.append(data_element.leader(leader))

            if isinstance(record, GroupableOrderedDict):
                items = record.iteritems(with_order=False, repeated=True)
            else:
                items = iteritems(record)

            for df, subfields in items:
                # Control fields
                if len(df) == 3:
                    if isinstance(subfields, string_types):
                        controlfield = data_element.controlfield(subfields)
                        controlfield.attrib['tag'] = df[:3]
                        rec_data.append(controlfield)
                    elif isinstance(subfields, (list, tuple, set)):
                        for subfield in subfields:
                            controlfield = data_element.controlfield(subfield)
                            controlfield.attrib['tag'] = df[:3]
                            rec_data.append(controlfield)
                else:
                    # Skip leader.
                    if df == 'leader':
                        continue

                    if not isinstance(subfields, (list, tuple, set)):
                        subfields = (subfields,)

                    df = df.replace('_', ' ')
                    for subfield in subfields:
                        if not isinstance(subfield, (list, tuple, set)):
                            subfield = [subfield]

                        for s in subfield:
                            datafield = data_element.datafield()
                            datafield.attrib['tag'] = df[:3]
                            datafield.attrib['ind1'] = df[3]
                            datafield.attrib['ind2'] = df[4]

                            if isinstance(s, GroupableOrderedDict):
                                items = s.iteritems(
                                    with_order=False, repeated=True)
                            elif isinstance(s, dict):
                                items = iteritems(s)
                            else:
                                datafield.append(data_element.subfield(s))

                                items = tuple()

                            for code, value in items:
                                if isinstance(value, string_types):
                                    datafield.append(data_element.subfield(
                                        strip_chars(value), code=code)
                                    )
                                else:
                                    for v in value:
                                        datafield.append(
                                            data_element.subfield(
                                                strip_chars(v), code=code)
                                        )
                            rec_data.append(datafield)
                rec_record_data.append(rec_data)
                rec.append(rec_record_data)
            rec.append(element.RecordPosition(str(idx)))
            return rec

        if isinstance(records, dict):
            root = dump_record(records, 1)
        else:
            number_of_records = total['value']
            start_record = sru.get('start_record', 0)
            maximum_records = sru.get('maximum_records', 0)
            query = sru.get('query')
            query_es = sru.get('query_es')
            next_record = start_record + maximum_records
            root = element.searchRetrieveResponse()
            root.append(element.version('1.1'))
            root.append(element.numberOfRecords(str(number_of_records)))
            if next_record > 1 and next_record < number_of_records:
                root.append(element.nextRecordPosition(str(next_record)))
            data = element.records()
            for idx, record in enumerate(records, start_record):
                data.append(dump_record(record, idx))
            root.append(data)
            echoed_search_rr = element.echoedSearchRetrieveRequest()
            if query:
                echoed_search_rr.append(element.query(query))
            if query_es:
                echoed_search_rr.append(element.query_es(query_es))
            if start_record:
                echoed_search_rr.append(
                    element.startRecord(str(start_record)))
            if maximum_records:
                echoed_search_rr.append(
                    element.maximumRecords(str(maximum_records)))
            echoed_search_rr.append(element.recordPacking('XML'))
            echoed_search_rr.append(
                element.recordSchema(
                    'info:sru/schema/1/marcxml-v1.1-light'))
            echoed_search_rr.append(element.resultSetTTL('0'))
            root.append(echoed_search_rr)

        # Needed if we use display with XSLT file.
        # if xslt_filename is not None:
        #     xslt_root = etree.parse(open(xslt_filename))
        #     transform = etree.XSLT(xslt_root)
        #     root = transform(root).getroot()

        return root

    def dumps(self, total, records, sru, xslt_filename=None, **kwargs):
        """Dump records into a MarcXMLSRU file."""
        root = self.dumps_etree(
            total=total,
            records=records,
            sru=sru,
            xslt_filename=xslt_filename
        )
        return etree.tostring(
            root,
            pretty_print=True,
            xml_declaration=True,
            encoding='UTF-8',
            **kwargs
        )

    def serialize_search(self, pid_fetcher, search_result,
                         item_links_factory=None, **kwargs):
        """Serialize a search result.

        :param pid_fetcher: Persistent identifier fetcher.
        :param search_result: Elasticsearch search result.
        :param item_links_factory: Factory function for the items in result.
            (Default: ``None``)
        :returns: The objects serialized.
        """
        language = request.args.get('ln', DEFAULT_LANGUAGE)
        with_holdings_items = not request.args.get('without_items', False)
        sru = search_result['hits'].get('sru', {})
        query_es = sru.get('query_es', '')
        organisation_pids = re.findall(
            r'holdings.organisation.organisation_pid:(\d*)',
            query_es, re.DOTALL)
        library_pids = re.findall(
            r'holdings.organisation.library_pid:(\d*)',
            query_es, re.DOTALL)
        location_pids = re.findall(
            r'holdings.location.pid:(\d*)',
            query_es, re.DOTALL)
        records = self.transform_records(
            hits=search_result['hits']['hits'],
            pid_fetcher=pid_fetcher,
            language=language,
            with_holdings_items=with_holdings_items,
            organisation_pids=organisation_pids,
            library_pids=library_pids,
            location_pids=location_pids,
            item_links_factory=item_links_factory
        )
        return self.dumps(
            total=search_result['hits']['total'],
            sru=sru,
            records=records,
            **self.dumps_kwargs
        )
