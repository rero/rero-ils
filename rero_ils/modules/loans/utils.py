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

"""Loans utils."""

from datetime import datetime, timedelta, timezone

import ciso8601

from ..circ_policies.api import CircPolicy
from ..items.api import Item
from ..libraries.api import Library
from ..patrons.api import Patron


def get_circ_policy(loan):
    """Return a circ policy for loan."""
    item = Item.get_record_by_pid(loan.get('item_pid'))
    holding_circulation_category = item.holding_circulation_category_pid
    library_pid = loan.library_pid
    patron = Patron.get_record_by_pid(loan.get('patron_pid'))
    patron_type_pid = patron.patron_type_pid

    result = CircPolicy.provide_circ_policy(
        library_pid,
        patron_type_pid,
        holding_circulation_category
    )

    # checkouts and request are not allowed anymore for blocked patrons
    if patron.get('blocked', False):
        result.update({
            "allow_checkout": False,
            "allow_requests": False,
        })

    return result


def get_default_loan_duration(loan):
    """Return calculated checkout duration in number of days."""
    # TODO: case when 'now' is not sysdate.
    now = datetime.utcnow()

    # Get library (to check opening hours and get timezone)
    library = Library.get_record_by_pid(loan.library_pid)

    # Process difference between now and end of day in term of hours/minutes
    #   - use hours and minutes from now
    #   - check regarding end of day (eod), 23:59
    #   - correct the hours/date regarding library timezone
    eod = timedelta(hours=23, minutes=59)
    aware_eod = eod - library.get_timezone().utcoffset(now, is_dst=True)
    time_to_eod = aware_eod - timedelta(hours=now.hour, minutes=now.minute)

    # Due date should be defined differently from checkout_duration
    # For that we use:
    #   - expected due date (now + checkout_duration)
    #   - next library open date (the eve of exepected due date is used)
    # We finally make the difference between next library open date and now.
    # We apply a correction for hour/minute to be 23:59 (end of day).
    policy = get_circ_policy(loan)

    # Should block checkouts when a circulation policy found with
    # allow_checkout is false.
    # In this case, a checkout duration of zero days is returned, this will
    #  trigger an HTTP 403 response for the frontend, thanks to
    #  loan_satisfy_circ_policies.

    if policy.get('allow_checkout') is True:
        due_date_eve = now + timedelta(days=policy.get(
            'checkout_duration')) - timedelta(days=1)
        next_open_date = library.next_open(date=due_date_eve)
        return timedelta(days=(next_open_date - now).days) + time_to_eod

    return timedelta(days=0)


def get_extension_params(loan=None, parameter_name=None):
    """Return extension parameters."""
    policy = get_circ_policy(loan)
    end_date = ciso8601.parse_datetime(loan.get('end_date'))
    params = {
        'max_count': policy.get('number_renewals'),
        'duration_default': policy.get('renewal_duration')
    }

    # Get library (to check opening hours)
    library = Library.get_record_by_pid(loan.library_pid)

    now = datetime.utcnow()
    # Fix end of day regarding Library timezone
    eod = timedelta(hours=23, minutes=59)
    aware_eod = eod - library.get_timezone().utcoffset(now, is_dst=True)
    time_to_eod = aware_eod - timedelta(hours=now.hour, minutes=now.minute)

    calculated_due_date = now + timedelta(
        days=policy.get('renewal_duration'))

    first_open_date = library.next_open(
        date=calculated_due_date - timedelta(days=1))

    if first_open_date.date() < end_date.date():
        params['max_count'] = 0

    new_duration = first_open_date - now
    params['duration_default'] = \
        timedelta(days=new_duration.days) + time_to_eod

    return params.get(parameter_name)


def extend_loan_data_is_valid(end_date, renewal_duration, library_pid):
    """Checks extend loan will be valid."""
    end_date = ciso8601.parse_datetime(end_date)
    current_date = datetime.now(timezone.utc)
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
