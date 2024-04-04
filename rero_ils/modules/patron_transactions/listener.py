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

"""Signals connector for Patron transaction."""

from .api import PatronTransaction, PatronTransactionsSearch


def enrich_patron_transaction_data(sender, json=None, record=None, index=None,
                                   doc_type=None, arguments=None,
                                   **dummy_kwargs):
    """Signal sent before a record is indexed.

    :param json: The dumped record dictionary which can be modified.
    :param record: The record being indexed.
    :param index: The index in which the record will be indexed.
    :param doc_type: The doc_type for the record.
    """
    if index.split('-')[0] != PatronTransactionsSearch.Meta.index:
        return

    if not isinstance(record, PatronTransaction):
        record = PatronTransaction.get_record_by_pid(record.get('pid'))

    if barcode := record.patron.patron.get('barcode'):
        json['patron']['barcode'] = barcode[0]

    if loan := record.loan:
        json['document'] = {'pid': record.document_pid, 'type': 'doc'}
        json['library'] = {'pid': record.library_pid, 'type': 'lib'}
        json['item'] = {'pid': loan.item_pid, 'type': 'item'}
