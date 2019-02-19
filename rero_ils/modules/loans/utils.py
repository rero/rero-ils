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

from datetime import datetime, timedelta

from ..circ_policies.api import CircPolicy
from ..items.api import Item
from ..libraries.api import Library
from ..patrons.api import Patron


def get_circ_policy(loan):
    """Return a circ policy for loan."""
    item = Item.get_record_by_pid(loan.item_pid)
    item_type_pid = item.item_type_pid
    library_pid = item.library_pid

    patron = Patron.get_record_by_pid(loan.patron_pid).replace_refs()
    patron_type_pid = patron.patron_type_pid

    return CircPolicy.provide_circ_policy(
        library_pid,
        patron_type_pid,
        item_type_pid
    )


def get_default_loan_duration(loan):
    """Return calculated checkout duration in number of days."""
    policy = get_circ_policy(loan)
    # TODO: case when start_date is not sysdate.
    start_date = datetime.now()
    library_pid = Item.get_record_by_pid(loan.item_pid).library_pid
    library = Library.get_record_by_pid(library_pid)
    # invenio-circulation due_date.
    due_date = start_date + timedelta(days=policy.get('checkout_duration'))
    # rero_ils due_date, considering library opening_hours and exception_dates.
    # next_open: -1 to check first the due date not the days.
    open_after_due_date = library.next_open(date=due_date - timedelta(days=1))

    new_duration = open_after_due_date - start_date

    return new_duration.days


def get_default_extension_duration(loan):
    """Return extension duration in number of days."""
    policy = get_circ_policy(loan)
    # TODO: case when start_date is not sysdate.
    start_date = datetime.now()
    library_pid = Item.get_record_by_pid(loan.item_pid).library_pid
    library = Library.get_record_by_pid(library_pid)
    # invenio-circulation due_date.
    due_date = start_date + timedelta(days=policy.get('renewal_duration'))
    # rero_ils due_date, considering library opening_hours and exception_dates.
    # next_open: -1 to check first the due date not the days.
    open_after_due_date = library.next_open(date=due_date - timedelta(days=1))
    new_duration = open_after_due_date - start_date

    return new_duration.days


def get_default_extension_max_count(loan):
    """Return extensions max count."""
    policy = get_circ_policy(loan)
    return policy.get('number_renewals')


def loan_satisfy_circ_policies(loan):
    """Validate the loan duration."""
    policy = get_circ_policy(loan)
    return loan['end_date'] > loan['start_date'] and \
        policy.get('allow_checkout')


def is_item_available_for_checkout(item_pid):
    """Item is available for action CHECKOUT."""
    item = Item.get_record_by_pid(item_pid).dumps()
    item_type_pid = item.get('item_type_pid')

    # item type no-checkout
    return item_type_pid != '4'
