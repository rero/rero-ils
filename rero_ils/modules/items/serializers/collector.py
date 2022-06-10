# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2022 RERO
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
from rero_ils.modules.item_types.api import ItemTypesSearch
from rero_ils.modules.items.models import ItemCirculationAction
from rero_ils.modules.libraries.api import LibrariesSearch
from rero_ils.modules.local_fields.api import LocalField
from rero_ils.modules.locations.api import LocationsSearch
from rero_ils.modules.operation_logs.api import OperationLogsSearch

from ..models import ItemNoteTypes


class Collecter(object):
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
        :return list of chuncked item pids and search records
        """
        records = []
        pids = []
        for result in results:
            pids.append(result.pid)
            records.append(result)
            if len(records) % cls.chunk_size == 0:
                yield pids, records
                pids = []
                records = []
        yield pids, records

    @classmethod
    def get_documents_by_item_pids(cls, item_pids, language):
        """Get documents for the given item pid list.

        :param item_pids: item pids.
        :param language: language.
        :return list of documents.
        """

        def _build_doc(data):
            document_data = {
                'document_title': next(
                    filter(
                        lambda x: x.get('type')
                        == 'bf:Title', data.get('title'))
                ).get('_text'),
                'document_masked': 'No'
            }
            # process contributions
            creator = []
            for contribution in data.get('contribution', []):
                if any(role in contribution.get('role')
                        for role in cls.role_filter):
                    authorized_access_point = \
                        f'authorized_access_point_{language}'
                    if authorized_access_point in contribution.get('agent'):
                        creator.append(
                            contribution['agent'][
                                authorized_access_point]
                        )
            document_data['document_creator'] = ' ; '.join(creator)
            document_main_type = []
            document_sub_type = []
            for document_type in data.get('type'):
                # data = document_type.to_dict()
                document_main_type.append(
                    document_type.get('main_type'))
                document_sub_type.append(
                    document_type.get('subtype', ''))
            document_data['document_main_type'] = ', '.join(
                document_main_type)
            document_data['document_sub_type'] = ', '.join(
                document_sub_type)
            # masked
            document_data['document_masked'] = \
                'Yes' if data.get('_masked') else 'No'
            # isbn:
            document_data['document_isbn'] = cls.separator.join(
                data.get('isbn', []))
            # issn:
            document_data['document_issn'] = cls.separator.join(
                data.get('issn', []))
            # document_series_statement
            document_data['document_series_statement'] = cls.separator.join(
                data['value']
                for serie in data.get('seriesStatement', [])
                for data in serie.get('_text', [])
            )
            # document_edition_statement
            document_data['document_edition_statement'] = cls.separator.join(
                edition.get('value')
                for edition_statement in
                data.get('editionStatement', [])
                for edition in edition_statement.get('_text', [])
            )
            # process provision activity
            provision_activity = next(
                filter(lambda x: x.get('type')
                       == 'bf:Publication', data.get('provisionActivity'))
            )
            start_date = provision_activity.get('startDate', '')
            end_date = provision_activity.get('endDate')
            document_data['document_publication_year'] = \
                f'{start_date} - {end_date}' \
                if end_date else start_date

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
                     'type', '_masked', 'isbn', 'issn'])
        docs = {}
        for doc in doc_search.scan():
            docs[doc.pid] = _build_doc(doc.to_dict())
        return docs

    @classmethod
    def mapper(cls):
        """Return mapping dictionaries.

        :return mapped item types, locations and libraries.
        """
        item_types_map = {
            item_type.pid: item_type.name
            for item_type in ItemTypesSearch().source(['pid', 'name']).scan()
        }
        locations_map = {
            location.pid: location.name
            for location in LocationsSearch().source(['pid', 'name']).scan()
        }
        libraries_map = {
            library.pid: library.name
            for library in LibrariesSearch().source(['pid', 'name']).scan()
        }
        return item_types_map, locations_map, libraries_map

    @classmethod
    def es_items_data(cls, hit):
        """Collect es items data."""
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
            'temporary_item_type_expiry_date': hit.get(
                'temporary_item_type', {}).get('end_date'),
            'item_masked': 'No'
        }
        fields = [
            ('pid', 'item_pid'),
            ('_created', 'item_create_date'),
            ('acquisition_date', 'item_acquisition_date'),
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

        # process notes
        for note in hit.get('notes', []):
            if note.get('type') in ItemNoteTypes.INVENTORY_LIST_CATEGORY:
                csv_data[f"item_{note.get('type')}"] = note.get(
                    'content')
        # item masking
        csv_data['item_masked'] = 'Yes' if hit.get('_masked') else 'No'

        return csv_data

    @classmethod
    def get_item_data(cls, hit, item_types_map):
        """Get item data.

        :param hit: item ES record.
        :param item_types_map: item types mapping.
        :return csv_data: dictionary of data.
        """
        csv_data = cls.es_items_data(hit)

        # process item type and temporary item type
        csv_data['item_type'] = item_types_map[
            csv_data.get('item_type_pid')]
        if temporary_item_type_pid := csv_data.pop(
                'temporary_item_type_pid', None):
            csv_data['temporary_item_type'] = item_types_map[
                temporary_item_type_pid]

        return csv_data

    @classmethod
    def append_issue_data(cls, csv_data):
        """Append issue data.

        :param csv_data: data dictionary.
        """
        # process item issue
        if csv_data['item_item_type'] != 'issue':
            return
        issue = csv_data['issue']
        if issue.get('inherited_first_call_number') \
                and not csv_data.get('item_call_number'):
            csv_data['item_call_number'] = \
                issue.get('inherited_first_call_number')
        csv_data['issue_status'] = issue.get('status')
        if issue.get('status_date'):
            csv_data['issue_status_date'] = \
                ciso8601.parse_datetime(
                    issue.get('status_date')).date()
        csv_data['issue_claims_count'] = \
            issue.get('claims_count', 0)
        csv_data['issue_expected_date'] = \
            issue.get('expected_date')
        csv_data['issue_regular'] = issue.get('regular')

    @classmethod
    def append_library_data(cls, csv_data, libraries_map):
        """Append library data.

        :param libraries_map: libraries mapping.
        :param csv_data: data dictionary.
        """
        csv_data['item_library_name'] = libraries_map[
            csv_data.pop('item_library_pid')]

    @classmethod
    def append_location_data(cls, csv_data, locations_map):
        """Append location data.

        :param locations_map: locations mapping.
        :param csv_data: data dictionary.
        """
        csv_data['item_location_name'] = locations_map[
            csv_data.pop('item_location_pid')]

    @classmethod
    def append_document_data(cls, csv_data, documents):
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
                '{message} on document: {pid}'.format(
                    message=err,
                    pid=hit['document']['pid'])
            )


    @classmethod
    def append_local_fields(cls, resource_type, resource_pid, csv_data):
        """Append item local fields data.

        :param csv_data: data dictionary.
        :param resource_type: resoruce_type.
        :param resource_pid: resource_pid.
        """
        org_pid = csv_data['item_org_pid']
        if local_fields := LocalField.get_local_fields_by_resource(
                resource_type, resource_pid, organisation_pid=org_pid):
            for field, num in itertools.product(local_fields, range(1, 11)):
                field_name = f'{resource_type}_local_field_{num}'
                if field_data := field.get('fields', {}).get(f'field_{num}'):
                    csv_data[field_name] = ' '.join(filter(None, field_data))

    @classmethod
    def get_loans_by_item_pids(cls, item_pids=None):
        """Get loans for the given item pid list.

        :param item_pids: item pids.
        :return list of checkouts, renewals, last_transaction_dates,
                last_checkouts.
        """
        checkouts_query = OperationLogsSearch()\
            .filter('term', loan__trigger__raw=ItemCirculationAction.CHECKOUT)\
            .filter('terms', loan__item__pid=item_pids)\
            .source(['loan.item.pid'])\
            .extra(rows=0)
        agg = A('terms', field='loan.item.pid', size=cls.chunk_size)
        checkouts_query.aggs.bucket('loans_count', agg)

        results = checkouts_query[:cls.chunk_size].execute()
        checkouts = {
            result.key: result.doc_count
            for result in results.aggregations.loans_count.buckets}

        renewals_query = OperationLogsSearch()\
            .filter('term', loan__trigger__raw=ItemCirculationAction.EXTEND)\
            .filter('terms', loan__item__pid=item_pids)\
            .source(['loan.item.pid'])\
            .extra(rows=0)
        agg = A('terms', field='loan.item.pid', size=cls.chunk_size)
        renewals_query.aggs.bucket('loans_count', agg)

        results = renewals_query[:cls.chunk_size].execute()
        renewals = {
            result.key: result.doc_count
            for result in results.aggregations.loans_count.buckets}

        last_transaction_dates = {}
        date_query = OperationLogsSearch()\
            .filter('terms', loan__item__pid=item_pids) \
            .sort({'_created': {"order": "desc"}})\
            .params(preserve_order=True)\
            .source(['loan.item.pid', 'date'])

        date_query = date_query.extra(
            collapse={
                'field': 'loan.item.pid',
                "inner_hits": {
                    "name": "most_recent",
                    "size": 1,
                    "sort": [{"date": "desc"}],
                }
            }
        )
        results = date_query[:cls.chunk_size].execute()
        for loan_hit in results:
            loan_data = loan_hit.to_dict()
            item_pid = loan_data['loan']['item']['pid']
            last_transaction_dates[item_pid] = {
                'last_transaction_date': ciso8601.parse_datetime(
                    loan_data['date']).date()
            }

        last_checkouts = {}
        last_checkout_query = OperationLogsSearch()\
            .filter('terms', loan__item__pid=item_pids) \
            .filter('term', loan__trigger__raw=ItemCirculationAction.CHECKOUT)\
            .sort({'_created': {"order": "desc"}})\
            .params(preserve_order=True)\
            .source(['loan.item.pid', 'date'])

        last_checkout_query = last_checkout_query.extra(
            collapse={
                'field': 'loan.item.pid',
                "inner_hits": {
                    "name": "most_recent",
                    "size": 1,
                    "sort": [{"date": "desc"}],
                }
            }
        )
        results = last_checkout_query[:cls.chunk_size].execute()
        for loan_hit in results:
            loan_data = loan_hit.to_dict()
            item_pid = loan_data['loan']['item']['pid']
            last_checkouts[item_pid] = {
                'checkout_date': ciso8601.parse_datetime(
                    loan_data['date']).date()
            }

        return checkouts, renewals, last_transaction_dates, last_checkouts
