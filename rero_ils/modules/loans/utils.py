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

import ciso8601
from dateutil.parser import parse
from flask import current_app

from ..circ_policies.api import CircPolicy
from ..items.api import Item
from ..libraries.api import Library
from ..locations.api import Location
from ..patrons.api import Patron, current_patron


def get_circ_policy(loan):
    """Return a circ policy for loan."""
    item = Item.get_record_by_pid(loan.get('item_pid'))
    item_type_pid = item.item_type_pid
    transaction_location_pid = loan.get('transaction_location_pid')
    if not transaction_location_pid:
        library_pid = item.library_pid
    else:
        library_pid = \
            Location.get_record_by_pid(transaction_location_pid).library_pid
    patron = Patron.get_record_by_pid(loan.get('patron_pid'))
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
    transaction_location_pid = loan.get('transaction_location_pid')
    if not transaction_location_pid:
        library_pid = Item.get_record_by_pid(loan.item_pid).library_pid
    else:
        library_pid = \
            Location.get_record_by_pid(transaction_location_pid).library_pid

    library = Library.get_record_by_pid(library_pid)
    # invenio-circulation due_date.
    due_date = start_date + timedelta(days=policy.get('checkout_duration'))
    # rero_ils due_date, considering library opening_hours and exception_dates.
    # next_open: -1 to check first the due date not the days.
    open_after_due_date = library.next_open(date=due_date - timedelta(days=1))

    new_duration = open_after_due_date - start_date

    return new_duration.days


def get_extension_params(loan=None, parameter_name=None):
    """Return extension parameters."""
    policy = get_circ_policy(loan)
    end_date = ciso8601.parse_datetime_as_naive(loan.get('end_date'))
    params = {
        'max_count': policy.get('number_renewals'),
        'duration_default': policy.get('renewal_duration')
    }
    current_date = datetime.now()

    transaction_location_pid = loan.get('transaction_location_pid')
    if not transaction_location_pid:
        library_pid = Item.get_record_by_pid(loan.item_pid).library_pid
    else:
        library_pid = \
            Location.get_record_by_pid(transaction_location_pid).library_pid
    library = Library.get_record_by_pid(library_pid)

    calculated_due_date = current_date + timedelta(
        days=policy.get('renewal_duration'))

    first_open_date = library.next_open(
        date=calculated_due_date - timedelta(days=1))

    if first_open_date.date() < end_date.date():
        params['max_count'] = 0

    new_duration = first_open_date - current_date
    params['duration_default'] = new_duration.days

    return params.get(parameter_name)


def extend_loan_data_is_valid(end_date, renewal_duration, library_pid):
    """Checks extend loan will be valid."""
    end_date = ciso8601.parse_datetime_as_naive(end_date)
    current_date = datetime.now()
    library = Library.get_record_by_pid(library_pid)
    calculated_due_date = current_date + timedelta(
        days=renewal_duration)
    first_open_date = library.next_open(
        date=calculated_due_date - timedelta(days=1))
    if first_open_date.date() <= end_date.date():
        return False
    return True


def loan_satisfy_circ_policies(loan):
    """Validate the loan duration."""
    policy = get_circ_policy(loan)
    return loan['end_date'] > loan['start_date'] and \
        policy.get('allow_checkout')


def is_item_available_for_checkout(item_pid):
    """Item is available for action CHECKOUT."""
    # TODO: implement item level restrictions not related to cipo here
    return True


def can_be_requested(loan):
    """Check if record can be requested."""
    if not loan.get('item_pid'):
        raise Exception('Transaction on document is not implemented.')
    policy = get_circ_policy(loan)
    return policy.get('allow_requests')
