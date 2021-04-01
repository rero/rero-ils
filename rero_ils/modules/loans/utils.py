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
import math
from datetime import datetime, timedelta, timezone

import ciso8601

from .api import get_any_loans_by_item_pid_by_patron_pid
from ..circ_policies.api import CircPolicy
from ..items.api import Item
from ..libraries.api import Library
from ..locations.api import Location
from ..patrons.api import Patron
from ..utils import get_ref_for_pid


def get_circ_policy(loan):
    """Return a circ policy for loan."""
    item = Item.get_record_by_pid(loan.item_pid)
    library_pid = loan.library_pid
    patron = Patron.get_record_by_pid(loan.get('patron_pid'))
    patron_type_pid = patron.patron_type_pid

    result = CircPolicy.provide_circ_policy(
        loan.organisation_pid,
        library_pid,
        patron_type_pid,
        item.temporary_item_type_pid or item.holding_circulation_category_pid
    )
    return result


def get_default_loan_duration(loan, initial_loan):
    """Return calculated checkout duration in number of days."""
    # TODO: case when 'now' is not sysdate.
    now = datetime.utcnow()

    # Get library (to check opening hours and get timezone)
    library = Library.get_record_by_pid(loan.library_pid)

    # Process difference between now and end of day in term of hours/minutes
    #   - use hours and minutes from now
    #   - check regarding end of day (eod), 23:59
    #   - correct the hours/date regarding library timezone
    eod = timedelta(hours=23, minutes=59, seconds=59, milliseconds=999)
    aware_eod = eod - library.get_timezone().utcoffset(now, is_dst=True)
    time_to_eod = aware_eod - timedelta(hours=now.hour, minutes=now.minute)

    # Due date should be defined differently from checkout_duration
    # For that we use:
    #   - expected due date (now + checkout_duration)
    #   - next library open date (the eve of expected due date is used)
    # We finally make the difference between next library open date and now.
    # We apply a correction for hour/minute to be 23:59 (end of day).

    # NOTE : Previously this function checks than the cipo allows checkout.
    #        This check is now done previously by `CircPolicies.allow_checkout`
    #        method. This was not the place for this ; this function should
    #        only return the loan duration.
    policy = get_circ_policy(loan)
    due_date_eve = now \
        + timedelta(days=policy.get('checkout_duration', 0)) \
        - timedelta(days=1)
    next_open_date = library.next_open(date=due_date_eve)
    return timedelta(days=(next_open_date - now).days) + time_to_eod


def get_extension_params(loan=None, initial_loan=None, parameter_name=None):
    """Return extension parameters."""
    policy = get_circ_policy(loan)
    end_date = ciso8601.parse_datetime(str(loan.get('end_date')))
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


def validate_loan_duration(loan):
    """Validate the loan duration."""
    return loan['end_date'] > loan['start_date']


def is_item_available_for_checkout(item_pid):
    """Item is available for action CHECKOUT."""
    # TODO: implement item level restrictions not related to cipo here
    return True


def can_be_requested(loan):
    """Check if record can be requested."""
    # TODO : Should use
    #  ``` item = Item.get_record_by_pid(loan.get('item_pid')
    #      can, reasons = item.can(ItemCirculationActions.REQUEST, loan=loan)
    #      return can
    #  ```
    #  But this usage cause a lot of problem with invenio-circulation because
    #  it seems this function only answer the question "Is the item potentially
    #  requestable" and not "Is the item is really requestable".

    if not loan.item_pid:
        raise Exception('Transaction on document is not implemented.')

    # 1) Check patron is not blocked
    patron = Patron.get_record_by_pid(loan.patron_pid)
    if patron.patron.get('blocked', False):
        return False

    # 2) Check if location allows request
    location = Location.get_record_by_pid(loan.location_pid)
    if not location or not location.get('allow_request'):
        return False

    # 3) Check if there is already a loan for same patron+item
    if get_any_loans_by_item_pid_by_patron_pid(
            loan.get('item_pid', {}).get('value'),
            loan.get('patron_pid')
    ):
        return False

    # 4) Check if circulation_policy allows request
    policy = get_circ_policy(loan)
    if not policy.get('allow_requests'):
        return False

    # All checks are successful, the request is allowed
    return True


def loan_build_item_ref(loan_pid, loan):
    """Build $ref for the Item attached to the Loan."""
    return get_ref_for_pid('items', loan.item_pid)


def loan_build_patron_ref(loan_pid, loan):
    """Build $ref for the Patron attached to the Loan."""
    return get_ref_for_pid('patrons', loan.patron_pid)


def loan_build_document_ref(loan_pid, loan):
    """Build $ref for the Document attached to the Loan."""
    return get_ref_for_pid('documents', loan.document_pid)


def validate_item_pickup_transaction_locations(loan, destination, **kwargs):
    """Validate the loan item, pickup and transaction locations.

    :param loan : the loan record to validate
    :param destination : transitition destination
    :param kwargs : all others named arguments
    :return: validation of the loan to next transition, True or False
    """
    pickup_library_pid = kwargs.get('pickup_library_pid', None)
    transaction_library_pid = kwargs.get('transaction_library_pid', None)

    # validation is made at the library level
    if not pickup_library_pid:
        pickup_location_pid = loan['pickup_location_pid']
        pickup_library_pid = Location.get_record_by_pid(
            pickup_location_pid).library_pid
    if not transaction_library_pid:
        transaction_location_pid = loan['transaction_location_pid']
        transaction_library_pid = Location.get_record_by_pid(
            transaction_location_pid).library_pid

    if destination == 'ITEM_AT_DESK':
        return pickup_library_pid == transaction_library_pid
    elif destination == 'ITEM_IN_TRANSIT_FOR_PICKUP':
        return pickup_library_pid != transaction_library_pid


def sum_for_fees(fee_steps):
    """Compute the sum of fee steps/intervals.

    :param fee_steps: an array of tuples. Each first tuple element should be
                      the amount to add (as a float).
    :return the sum of fee steps rounded with a precision of 2 digits after
            decimal
    """
    if fee_steps:
        return round(math.fsum([fee[0] for fee in fee_steps]), 2)
    else:
        return 0
