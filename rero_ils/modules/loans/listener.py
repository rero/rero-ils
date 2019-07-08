# -*- coding: utf-8 -*-
#
# This file is part of RERO ILS.
# Copyright (C) 2017 RERO.
#
# RERO ILS is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# RERO ILS is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RERO ILS; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Signals connector for Loan."""

from invenio_circulation.proxies import current_circulation

from ..items.api import Item
from ..loans.api import Loan
from ..locations.api import Location


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
        location_pid = item.replace_refs()['location']['pid']
        location = Location.get_record_by_pid(location_pid).replace_refs()
        json['library_pid'] = location['library']['pid']


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
