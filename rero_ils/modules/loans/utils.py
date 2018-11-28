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

"""Loans utils."""


from datetime import timedelta

from ..items.api import Item


def get_default_loan_duration(loan):
    """Return a default loan duration in number of days."""
    item = Item.get_record_by_pid(loan.get('item_pid')).dumps()
    item_type_pid = item.get('item_type_pid')
    if item_type_pid == '2':
        # item type short
        duration = 15
    else:
        duration = 30
    return duration


def get_default_extension_duration(loan):
    """Return a default extension duration in number of days."""
    item = Item.get_record_by_pid(loan.get('item_pid')).dumps()
    item_type_pid = item.get('item_type_pid')
    if item_type_pid == '2':
        duration = 15
    else:
        duration = 30
    return duration


def get_default_extension_max_count(loan):
    """Return a default extensions max count."""
    return float('inf')


def is_loan_duration_valid(loan):
    """Validate the loan duration."""
    return loan['end_date'] > loan['start_date'] and \
        loan['end_date'] - loan['start_date'] < timedelta(days=60)


def is_item_available_for_checkout(item_pid):
    """Item is available for action CHECKOUT."""
    item = Item.get_record_by_pid(item_pid).dumps()
    item_type_pid = item.get('item_type_pid')

    # item type no-checkout
    return item_type_pid != '4'
