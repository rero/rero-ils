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

"""Item collector."""


import itertools

import ciso8601
from elasticsearch_dsl import A
from flask import current_app

from rero_ils.modules.documents.api import DocumentsSearch
from rero_ils.modules.local_fields.api import LocalField
from rero_ils.modules.operation_logs.api import OperationLogsSearch

from ..models import ItemCirculationAction, ItemNoteTypes
from ...notifications.api import NotificationsSearch


class Collector():
    """collect data for csv."""

    # define chunk size
    chunk_size = 1000
    separator = ' | '

    role_filter = [
        'rsp',
        'cre',
        'enj',
        'dgs',
        'prg',
        'dsr',
        'ctg',
        'cmp',
        'inv',
        'com',
        'pht',
        'ivr',
        'art',
        'ive',
        'chr',
        'aut',
        'arc',
        'fmk',
        'pra',
        'csl'
    ]

    @classmethod
    def batch(cls, results):
        """Chunk search results.

        :param results: search results.
        :return list of chunked item pids and search records
        """
        records, pids = [], []
        for result in results:
            pids.append(result.pid)
            records.append(result)
            if len(records) % cls.chunk_size == 0:
                yield pids, records
                records, pids = [], []
        yield pids, records

    @classmethod
    def get_documents_by_item_pids(cls, item_pids, language):
        """Get documents for the given item pid list.

        :param item_pids: item pids.
        :param language: language.
        :return list of documents.
        """

        def _build_doc(data):
            document_data = {}
            # document title
            document_titles = filter(
                lambda t: t.get('type') == 'bf:Title',
                data.get('title', {})
            )
            if title := next(document_titles):
                document_data['document_title'] = title.get('_text')

            # document masked
            bool_values = ('No', 'Yes')
            is_masked = data.get('masked', False)
            document_data['document_masked'] = bool_values[is_masked]

            # process contributions
            creator = []
            for contribution in data.get('contribution', []):
                if any(role in contribution.get('role')
                        for role in cls.role_filter):
                    authorized_access_point = \
                        f'authorized_access_point_{language}'
                    if authorized_access_point in contribution.get('entity'):
                        creator.append(
                            contribution['entity'][
                                authorized_access_point]
                        )
            document_data['document_creator'] = ' ; '.join(creator)

            # document type/subtypes
            doc_types = []
            doc_subtypes = []
            for document_type in data.get('type'):
                doc_types.append(document_type.get('main_type'))
                doc_subtypes.append(document_type.get('subtype'))
            if doc_types := filter(None, doc_types):
                document_data['document_main_type'] = ', '.join(doc_types)
            if doc_subtypes := filter(None, doc_subtypes):
                document_data['document_sub_type'] = ', '.join(doc_subtypes)

            # identifiers
            document_data |= {
                'document_isbn': cls.separator.join(data.get('isbn', [])),
                'document_issn': cls.separator.join(data.get('issn', []))
            }

            # document_series_statement
            document_data['document_series_statement'] = cls.separator.join(
                data['value']
                for serie in data.get('seriesStatement', [])
                for data in serie.get('_text', [])
            )

            # document_edition_statement
            document_data['document_edition_statement'] = cls.separator.join(
                edition.get('value')
                for edition_statement in data.get('editionStatement', [])
                for edition in edition_statement.get('_text', [])
            )

            # provision activity
            #   we only use the first provision activity of type
            #   `bf:publication`
            publications = [
                prov for prov in data.get('provisionActivity', [])
                if prov.get('type') == 'bf:Publication'
            ]
            if provision_activity := next(iter(publications), None):
                start_date = provision_activity.get('startDate', '')
                end_date = provision_activity.get('endDate')
                document_data['document_publication_year'] = \
                    f'{start_date} - {end_date}' if end_date else start_date

                document_data['document_publisher'] = cls.separator.join(
                    data['value']
                    for stmt in provision_activity.get('statement', [])
                    for data in stmt.get('label', [])
                    if stmt['type'] == 'bf:Agent'
                )
            return document_data

        doc_search = DocumentsSearch() \
            .filter('terms', holdings__items__pid=list(item_pids)) \
            .source(['pid', 'title', 'contribution', 'provisionActivity',
                     'type', '_masked', 'isbn', 'issn', 'seriesStatement',
                     'editionStatement'])
        docs = {}
        for doc in doc_search.scan():
            docs[doc.pid] = _build_doc(doc.to_dict())
        return docs

    @staticmethod
    def get_item_data(hit):
        """Collect es items data.

        :param hit: ES item hit.
        :return csv_data: dictionary of data.
        """
        hit = hit.to_dict()
        csv_data = {
            'item_create_date': ciso8601.parse_datetime(
                hit['_created']).date(),
            'item_type_pid': hit.get('item_type', {}).get('pid'),
            'item_library_pid': hit.get('library', {}).get('pid'),
            'item_location_pid': hit.get('location', {}).get('pid'),
            'document_pid': hit.get('document', {}).get('pid'),
            'item_holding_pid': hit.get('holding', {}).get('pid'),
            'item_org_pid': hit.get('organisation', {}).get('pid'),
            'temporary_item_type_pid': hit.get(
                'temporary_item_type', {}).get('pid'),
            'item_masked': 'No',
            'item_status': hit.get('status'),
            'issue': hit.get('issue', {}),
            'current_pending_requests': hit.get('current_pending_requests', 0)
        }
        fields = [
            ('pid', 'item_pid'),
            ('barcode', 'item_barcode'),
            ('call_number', 'item_call_number'),
            ('second_call_number', 'item_second_call_number'),
            ('legacy_checkout_count', 'item_legacy_checkout_count'),
            ('pac_code', 'item_pac_code'),
            ('price', 'item_price'),
            ('type', 'item_item_type'),
            ('enumerationAndChronology', 'item_enumerationAndChronology')
        ]
        for field_name, new_field_name in fields:
            csv_data[new_field_name] = hit.get(field_name)
        # dates fields
        if end_date := hit.get('temporary_item_type', {}).get('end_date'):
            csv_data['temporary_item_type_expiry_date'] = \
                ciso8601.parse_datetime(end_date).date()
        if acquisition_date := hit.get('acquisition_date'):
            csv_data['item_acquisition_date'] = \
                ciso8601.parse_datetime(acquisition_date).date()
        if item_create_date := hit.get('_created'):
            csv_data['item_create_date'] = \
                ciso8601.parse_datetime(item_create_date).date()

        # process notes
        for note in hit.get('notes', []):
            if note.get('type') in ItemNoteTypes.INVENTORY_LIST_CATEGORY:
                csv_data[f"item_{note.get('type')}"] = note.get(
                    'content')
        # item masking
        csv_data['item_masked'] = 'Yes' if hit.get('_masked') else 'No'

        return csv_data

    @staticmethod
    def append_issue_data(hit, csv_data):
        """Append issue data.

        :param csv_data: data dictionary.
        """
        # process item issue
        if csv_data['item_item_type'] != 'issue':
            return
        issue = csv_data.pop('issue', None)
        if issue.get('inherited_first_call_number') \
                and not csv_data.get('item_call_number'):
            csv_data['item_call_number'] = \
                issue.get('inherited_first_call_number')
        csv_data['issue_status'] = issue.get('status')
        if issue.get('status_date'):
            csv_data['issue_status_date'] = \
                ciso8601.parse_datetime(
                    issue.get('status_date')).date()
        csv_data['issue_claims_count'] = NotificationsSearch()\
            .get_claims_count(csv_data['item_pid'])
        csv_data['issue_expected_date'] = \
            issue.get('expected_date')
        csv_data['issue_regular'] = issue.get('regular')

    @staticmethod
    def append_document_data(csv_data, documents):
        """Append document data.

        :param csv_data: data dictionary.
        :param documents: documents data.
        """
        try:
            # update csv data with document
            csv_data.update(documents.get(csv_data.get('document_pid')))
        except Exception as err:
            current_app.logger.error(
                'ERROR in csv serializer: '
                f'{message} on document: {csv_data.get("document_pid")}'
            )

    @classmethod
    def append_local_fields(cls, csv_data):
        """Append local fields data.

        :param csv_data: data dictionary.
        """
        def _append_res_local_fields(resource_type, resource_pid, csv_data):
            """Append local fields data.

            :param csv_data: data dictionary.
            :param resource_type: resource_type.
            :param resource_pid: resource_pid.
            """
            lf_type = 'document' if resource_type == 'doc' else resource_type
            org_pid = csv_data['item_org_pid']
            local_fields = LocalField.get_local_fields_by_id(
                    resource_type, resource_pid, organisation_pid=org_pid)
            for field, num in itertools.product(local_fields, range(1, 11)):
                field_name = f'{lf_type}_local_field_{num}'
                if field_data := field.get('fields', {}).get(f'field_{num}'):
                    csv_data[field_name] = cls.separator.join(field_data)

        _append_res_local_fields('item', csv_data['item_pid'], csv_data)
        _append_res_local_fields('doc', csv_data['document_pid'], csv_data)

    @staticmethod
    def get_loans_by_item_pids(item_pids=None, chunk_size=200):
        """Get loans for the given item pid list.

        :param item_pids: item pids.
        :return list of dicts of item statistics.
        """
        def _get_loans_by_item_pids(pids):
            # initial es query to return all loans for the given item_pids
            query = OperationLogsSearch()\
                .filter('terms', loan__item__pid=pids)
            # adds checkouts aggregation
            checkout_agg = A(
                'filter',
                term={'loan.trigger': ItemCirculationAction.CHECKOUT},
                aggs=dict(
                    item_pid=A(
                        'terms', field='loan.item.pid',
                        size=chunk_size,
                        aggs=dict(last_op=A('max', field='date')))))
            query.aggs.bucket('checkout', checkout_agg)
            # adds renewal aggregation
            renewal_agg = A(
                'filter',
                term={'loan.trigger': ItemCirculationAction.EXTEND},
                aggs=dict(item_pid=A(
                    'terms', size=chunk_size, field='loan.item.pid')))
            query.aggs.bucket('renewal', renewal_agg)
            # adds last transaction aggregation for the fours triggers below.
            triggers = [
                ItemCirculationAction.CHECKOUT,
                ItemCirculationAction.CHECKIN,
                ItemCirculationAction.EXTEND
            ]
            loans_agg = A(
                'filter', terms={'loan.trigger': triggers}, aggs=dict(
                    item_pid=A(
                        'terms',
                        field='loan.item.pid',
                        size=chunk_size,
                        aggs=dict(last_op=A('max', field='date')))))
            query.aggs.bucket('loans', loans_agg)
            # query execution
            result = query[0:0].execute()
            # dump output into a dict
            # checkouts data
            items_stats = {
                term.key: {
                    'checkout_count': term.doc_count,
                    'last_checkout': ciso8601.parse_datetime(
                        term.last_op.value_as_string).date()}
                for term in result.aggregations.checkout.item_pid
            }
            # renewal data
            for term in result.aggregations.renewal.item_pid:
                items_stats.setdefault(term.key, {})
                items_stats[term.key]['renewal_count'] = term.doc_count
            # last_transaction data
            for term in result.aggregations.loans.item_pid:
                items_stats.setdefault(term.key, {})
                items_stats[term.key]['last_transaction'] = \
                    ciso8601.parse_datetime(
                        term.last_op.value_as_string).date()
            return items_stats

        chunk_pids = []
        for pid in item_pids:
            if len(chunk_pids) % chunk_size == 0:
                stats = _get_loans_by_item_pids(chunk_pids)
                for pid in chunk_pids:
                    yield stats.get(pid, {})
                chunk_pids = []
            chunk_pids.append(pid)
        stats = _get_loans_by_item_pids(chunk_pids)
        for pid in chunk_pids:
            yield stats.get(pid, {})

    @staticmethod
    def append_loan_data(hit, csv_data, items_stats):
        """Append item loan.

        :param hit: item ES record.
        :param csv_data: dictionary of data.
        :param loans: loans data.
        """
        stat = next(items_stats)
        csv_data['item_checkouts_count'] = stat.get('checkout_count', 0)
        csv_data['item_renewals_count'] = stat.get('renewal_count', 0)
        csv_data['last_transaction_date'] = stat.get('last_transaction')
        csv_data['last_checkout_date'] = stat.get('last_checkout')
