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

"""Signals connector for Loan."""

from flask import current_app
from invenio_circulation.proxies import current_circulation

from ..items.api import Item
from ..loans.logs.api import LoanOperationLog
from ..patron_transactions.api import PatronTransaction


def enrich_loan_data(sender, json=None, record=None, index=None,
                     doc_type=None, arguments=None, **dummy_kwargs):
    """Signal sent before a record is indexed.

    :param json: The dumped record dictionary which can be modified.
    :param record: The record being indexed.
    :param index: The index in which the record will be indexed.
    :param doc_type: The doc_type for the record.
    """
    if index.split('-')[0] == current_circulation.loan_search_cls.Meta.index:
        item_pid = record.get('item_pid', {}).get('value')
        item = Item.get_record_by_pid(item_pid)
        if item:
            json['library_pid'] = item.holding_library_pid
        else:
            current_app.logger.warning(
                f'No item found: {item_pid} for loan: {record.get("pid")}')


def listener_loan_state_changed(
        _, initial_loan, loan, trigger, **transition_kwargs):
    """Create notification based on loan state changes.

    :param initial_loan: The inital loan.
    :param loan: The new loan.
    :param trigger: action trigger.
    :param transition_kwargs: An additional kwargs to transition.
    """
    # Create patron a librarian notifications
    loan.create_notification(trigger)

    # Create fees for checkin or extend operations
    if trigger in ['checkin', 'extend']:
        PatronTransaction.create_patron_transaction_from_overdue_loan(
            initial_loan
        )

    LoanOperationLog.create(loan)
