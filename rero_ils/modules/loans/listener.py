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

from invenio_circulation.proxies import current_circulation

from ..items.api import Item
from ..loans.api import Loan


def enrich_loan_data(sender, json=None, record=None, index=None,
                     **dummy_kwargs):
    """Signal sent before a record is indexed.

    :params json: The dumped record dictionary which can be modified.
    :params record: The record being indexed.
    :params index: The index in which the record will be indexed.
    :params doc_type: The doc_type for the record.
    """
    loan_index_name = current_circulation.loan_search.Meta.index
    if index.startswith(loan_index_name):
        item = Item.get_record_by_pid(record.get('item_pid'))
        json['library_pid'] = item.holding_library_pid


def listener_loan_state_changed(_, prev_loan, loan, trigger):
    """Create notification based on loan state changes."""
    if loan.get('state') == 'PENDING':
        item_pid = loan.get('item_pid')
        checkedout_loan_pid = Item.get_loan_pid_with_item_on_loan(item_pid)
        if checkedout_loan_pid:
            checked_out_loan = Loan.get_record_by_pid(checkedout_loan_pid)
            checked_out_loan.create_notification(notification_type='recall')
    elif loan.get('state') == 'ITEM_AT_DESK':
        loan.create_notification(notification_type='availability')
