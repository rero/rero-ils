# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
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

"""Signals connector for Patron transaction event."""

from .api import PatronTransactionEventsSearch
from ..patron_transactions.api import PatronTransactionsSearch


def enrich_patron_transaction_event_data(sender, json=None, record=None,
                                         index=None, doc_type=None,
                                         arguments=None, **dummy_kwargs):
    """Signal sent before a record is indexed.

    :param json: The dumped record dictionary which can be modified.
    :param record: The record being indexed.
    :param index: The index in which the record will be indexed.
    :param doc_type: The doc_type for the record.
    """
    if index.split('-')[0] == PatronTransactionEventsSearch.Meta.index:
        # ES search reduces number of requests for organisation and patron.
        es_patron_transaction = next(PatronTransactionsSearch().filter(
            'term', pid=json['parent']['pid']
        ).scan())
        json['organisation'] = {
            'pid': es_patron_transaction.organisation.pid
        }
        json['patron'] = {
            'pid': es_patron_transaction.patron.pid
        }
