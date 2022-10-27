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

"""Acquisition order serialization."""

import csv

from flask import current_app, request, stream_with_context
from invenio_i18n.ext import current_i18n
from invenio_records_rest.serializers.csv import CSVSerializer, Line

from rero_ils.modules.acquisition.acq_accounts.api import AcqAccountsSearch
from rero_ils.modules.acquisition.acq_order_lines.api import \
    AcqOrderLinesSearch
from rero_ils.modules.acquisition.acq_receipt_lines.api import \
    AcqReceiptLinesSearch
from rero_ils.modules.acquisition.acq_receipts.api import AcqReceiptsSearch
from rero_ils.modules.commons.identifiers import IdentifierStatus
from rero_ils.modules.documents.api import DocumentsSearch
from rero_ils.modules.documents.serializers.base import DocumentFormatter
from rero_ils.modules.vendors.api import VendorsSearch
from rero_ils.utils import get_i18n_supported_languages

creator_role_filter = [
    'rsp', 'cre', 'enj', 'dgs', 'prg', 'dsr', 'ctg', 'cmp', 'inv', 'com',
    'pht', 'ivr', 'art', 'ive', 'chr', 'aut', 'arc', 'fmk', 'pra', 'csl'
]


class AcqOrderCSVSerializer(CSVSerializer):
    """Mixin serializing records as CSV."""

    def serialize_search(self, pid_fetcher, search_result, links=None,
                         item_links_factory=None):
        """Serialize a search result.

        :param pid_fetcher: Persistent identifier fetcher.
        :param search_result: Elasticsearch search result.
        :param links: Dictionary of links to add to response.
        :param item_links_factory: Factory function for record links.
        """
        # define chunk size
        chunk_size = 100
        vendors = {}

        # language
        language = request.args.get("lang", current_i18n.language)
        if not language or language not in get_i18n_supported_languages():
            language = current_app.config.get('BABEL_DEFAULT_LANGUAGE', 'en')

        order_fields = {
            'order_pid': 'pid',
            'order_reference': 'reference',
            'order_date': 'order_date',
            'order_type': 'type',
            'order_status': 'status'
        }

        def generate_csv():
            def batch(results):
                """Chunk search results.

                :param results: search results.
                :return list of chunked item pids and search records
                """
                records = {}
                pids = []
                for result in results:
                    data = result.to_dict()
                    pids.append(data['pid'])
                    records[data['pid']] = data
                    if len(records) % chunk_size == 0:
                        yield pids, records
                        pids = []
                        records = {}
                yield pids, records

            def get_linked_records_by_order_pids(order_pids):
                """Get linked resources for the given order pids."""
                order_line_fields = [
                    'pid', 'quantity', 'amount', 'total_amount', 'status',
                    'priority', 'notes', 'document', 'acq_account',
                    'acq_order'
                ]
                records = AcqOrderLinesSearch() \
                    .get_records_by_terms(terms=order_pids,
                                          key='acq_order__pid',
                                          fields=order_line_fields)
                order_lines = {}
                doc_pids = []
                account_pids = []
                for result in records:
                    order_lines[result.pid] = result.to_dict()
                    doc_pids.append(result.document.pid)
                    account_pids.append(result.acq_account.pid)

                docs = get_documents_by_pids(doc_pids)
                accounts = get_accounts_by_pids(account_pids)
                receipt_lines = get_receipt_lines_by_order_line_pids(
                    list(order_lines.keys()))
                return order_lines, docs, accounts, receipt_lines

            def get_documents_by_pids(doc_pids):
                """Get documents for the given pids."""
                fields = [
                    'pid', 'contribution', 'editionStatement', 'identifiedBy',
                    'provisionActivity', 'seriesStatement', 'title'
                ]
                records = DocumentsSearch() \
                    .get_records_by_terms(terms=doc_pids, fields=fields)
                return {
                    record.pid: OrderDocumentFormatter(
                        record=record.to_dict(),
                        language=language).format()
                    for record in records
                }

            def get_accounts_by_pids(account_pids):
                """Get accounts for the given pids."""
                fields = ['pid', 'name', 'number']
                return AcqAccountsSearch()\
                    .get_records_by_terms(terms=account_pids, fields=fields,
                                          as_dict=True)

            def get_receipts_by_order_pids(order_pids):
                """Get receipts for the given pids."""
                fields = ['pid', 'reference']
                return AcqReceiptsSearch() \
                    .get_records_by_terms(terms=order_pids,
                                          key='acq_order__pid',
                                          fields=fields,
                                          as_dict=True)

            def get_receipt_lines_by_order_line_pids(order_lines_pids):
                """Get receipts for the given order lines pids."""
                fields = ['pid', 'quantity', 'receipt_date', 'total_amount',
                          'acq_order_line', 'acq_receipt']
                receipt_line_results = AcqReceiptLinesSearch() \
                    .get_records_by_terms(terms=order_lines_pids,
                                          key='acq_order_line__pid',
                                          fields=fields)
                # organize receipt lines by order line pid
                receipt_lines = {}
                for record in receipt_line_results:
                    key = record.acq_order_line.pid
                    data = receipt_lines.get(key, [])
                    data.append(record.to_dict())
                    receipt_lines[key] = data
                return receipt_lines

            def get_vendors_by_pids(vendor_pids):
                """Get vendors for the given pids."""
                fields = ['pid', 'name']
                return VendorsSearch() \
                    .get_records_by_terms(terms=vendor_pids, fields=fields,
                                          as_dict=True)

            headers = dict.fromkeys(self.csv_included_fields)

            # write the CSV output in memory
            line = Line()
            writer = csv.DictWriter(line,
                                    quoting=csv.QUOTE_ALL,
                                    fieldnames=headers)
            writer.writeheader()
            yield line.read()

            for pids, order_batch_results in batch(search_result):
                order_lines, documents, accounts, receipt_lines = \
                    get_linked_records_by_order_pids(pids)
                receipts = get_receipts_by_order_pids(pids)
                # vendors
                vendor_pids = [order['vendor']['pid']
                               for order in order_batch_results.values()
                               if order['vendor']['pid'] not in vendors]
                vendors.update(get_vendors_by_pids(vendor_pids))

                # prepare export based on order lines
                for order_line_pid, order_line in order_lines.items():
                    order_pid = order_line['acq_order']['pid']
                    order_data = order_batch_results[order_pid]
                    vendor_data = vendors.get(order_data['vendor']['pid'])

                    csv_data = {
                        k: order_data.get(f) for k, f in order_fields.items()
                    }

                    # Update csv data with vendor
                    csv_data['vendor_name'] = vendor_data.get('name')

                    # extract order notes
                    order_notes = filter(
                        lambda x: x.get('source').get('type') == 'acor',
                        order_data.get('notes', {})
                    )
                    for note in order_notes:
                        note_type = note.get('type')
                        column_name = f'order_{note_type}'
                        csv_data[column_name] = note.get('content')

                    # update csv data with document infos
                    csv_data.update(
                        documents.get(order_line['document']['pid']))

                    # update csv data with account infos
                    account = accounts.get(order_line['acq_account']['pid'])
                    csv_data.update({
                        'account_name': account.get('name'),
                        'account_number': account.get('number'),
                    })

                    # update csv data with order line infos
                    csv_data.update({
                        'order_lines_priority': order_line.get('priority'),
                        'order_lines_notes': ' | '.join(
                            f"{note['type']}: {note['content']}"
                            for note in order_line.get('notes', [])
                        ),
                        'order_lines_status': order_line['status'],
                        'ordered_quantity': order_line['quantity'],
                        'ordered_unit_price': order_line['amount'],
                        'ordered_amount': order_line['total_amount'],

                    })

                    # if we are receipt lines, we need to iterate on
                    # and return csv row
                    receipt_line_data = receipt_lines.get(order_line_pid)
                    if receipt_line_data:
                        for receipt_line in receipt_line_data:
                            receipt = receipts\
                                .get(receipt_line['acq_receipt']['pid'])
                            csv_data.update({
                                'received_amount':
                                    receipt_line['total_amount'],
                                'received_quantity':
                                    receipt_line['quantity'],
                                'receipt_reference': receipt['reference'],
                                'receipt_date': receipt_line['receipt_date'],
                            })
                            writer.writerow(self.process_dict(csv_data))
                            yield line.read()
                    else:
                        # write csv data
                        writer.writerow(self.process_dict(csv_data))
                        yield line.read()
        # return streamed content
        return stream_with_context(generate_csv())


class OrderDocumentFormatter(DocumentFormatter):
    """Document formatter class for orders."""

    # separator between multiple values
    _separator = ' | '

    def __init__(self, record, language=None, _include_fields=None):
        """Initialize RIS formatter with the specific record."""
        super().__init__(record)
        self._language = language or current_app\
            .config.get('BABEL_DEFAULT_LANGUAGE', 'en')
        self._include_fields = _include_fields or [
            'document_pid', 'document_creator', 'document_title',
            'document_publisher', 'document_publication_year',
            'document_edition_statement', 'document_series_statement',
            'document_isbn'
        ]

    def post_process(self, data):
        """Post process data."""
        # join multiple values in data if needed."""
        return self._separator.join(map(str, data)) \
            if isinstance(data, list) else data

    def _get_isbn(self, states=None):
        """Return ISBN identifiers for the given states."""
        return super()._get_isbn(states=IdentifierStatus.ALL)
