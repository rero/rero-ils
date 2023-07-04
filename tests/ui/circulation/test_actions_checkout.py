# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2020 RERO
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

"""Circulation tests."""

from copy import deepcopy
from datetime import date, timedelta

import pytest
from invenio_circulation.errors import ItemNotAvailableError, \
    NoValidTransitionAvailableError, TransitionConstraintsViolationError
from invenio_circulation.ext import NoValidTransitionAvailableError
from utils import item_record_to_a_specific_loan_state

from rero_ils.modules.items.api import Item
from rero_ils.modules.items.models import ItemStatus
from rero_ils.modules.loans.api import Loan
from rero_ils.modules.loans.models import LoanAction, LoanState


def test_checkout_library_never_open(
        circulation_policies,
        patron_martigny,
        lib_martigny,
        item_lib_martigny,
        loc_public_martigny,
        librarian_martigny
        ):
    """Test checkout from a library without opening hours."""

    # Test checkout if library has no open days but has exception days/hours
    # in the past
    lib_martigny['opening_hours'] = [
        {
            "day": "monday",
            "is_open": False,
            "times": []
        },
        {
            "day": "tuesday",
            "is_open": False,
            "times": []
        },
        {
            "day": "wednesday",
            "is_open": False,
            "times": []
        },
        {
            "day": "thursday",
            "is_open": False,
            "times": []
        },
        {
            "day": "friday",
            "is_open": False,
            "times": []
        },
        {
            "day": "saturday",
            "is_open": False,
            "times": []
        },
        {
            "day": "sunday",
            "is_open": False,
            "times": []
        }
    ]
    lib_martigny.commit()

    data = deepcopy(item_lib_martigny)
    data.pop('barcode')
    data.setdefault('status', ItemStatus.ON_SHELF)
    created_item = Item.create(
        data=data, dbcommit=True, reindex=True, delete_pid=True)

    params = {
        'patron_pid': patron_martigny.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid,
        'pickup_location_pid': loc_public_martigny.pid
    }
    onloan_item, actions = created_item.checkout(**params)
    loan = Loan.get_record_by_pid(actions[LoanAction.CHECKOUT].get('pid'))

    # check that can_extend method does not raise exception
    assert Loan.can_extend(onloan_item)[0] in [True, False]

    # check loan is ITEM_ON_LOAN and item is ON_LOAN
    assert onloan_item.status == ItemStatus.ON_LOAN
    assert loan['state'] == LoanState.ITEM_ON_LOAN

    # test checkout if library has no open days but has exception closed day
    # in the future
    exception_date = (date.today() + timedelta(days=30)).isoformat()
    lib_martigny['exception_dates'].append(
        {
            "title": "Closed",
            "is_open": False,
            "start_date": exception_date
        }
    )
    lib_martigny.commit()

    data = deepcopy(item_lib_martigny)
    data.pop('barcode')
    data.setdefault('status', ItemStatus.ON_SHELF)
    created_item = Item.create(
        data=data, dbcommit=True, reindex=True, delete_pid=True)

    params = {
        'patron_pid': patron_martigny.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid,
        'pickup_location_pid': loc_public_martigny.pid
    }
    onloan_item, actions = created_item.checkout(**params)
    loan = Loan.get_record_by_pid(actions[LoanAction.CHECKOUT].get('pid'))

    # check loan is ITEM_ON_LOAN and item is ON_LOAN
    assert onloan_item.status == ItemStatus.ON_LOAN
    assert loan['state'] == LoanState.ITEM_ON_LOAN

    # test checkout if library has no open days and no exception days/hours
    del lib_martigny['exception_dates']
    lib_martigny.commit()

    data = deepcopy(item_lib_martigny)
    data.pop('barcode')
    data.setdefault('status', ItemStatus.ON_SHELF)
    created_item = Item.create(
        data=data, dbcommit=True, reindex=True, delete_pid=True)

    params = {
        'patron_pid': patron_martigny.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid,
        'pickup_location_pid': loc_public_martigny.pid
    }
    onloan_item, actions = created_item.checkout(**params)
    loan = Loan.get_record_by_pid(actions[LoanAction.CHECKOUT].get('pid'))

    # check loan is ITEM_ON_LOAN and item is ON_LOAN
    assert onloan_item.status == ItemStatus.ON_LOAN
    assert loan['state'] == LoanState.ITEM_ON_LOAN

    from invenio_db import db
    db.session.rollback()


def test_checkout_on_item_on_shelf(
        circulation_policies,
        patron_martigny,
        patron2_martigny,
        item_lib_martigny,
        loc_public_martigny,
        librarian_martigny,
        item_on_shelf_martigny_patron_and_loan_pending):
    """Test checkout on an ON_SHELF item."""
    # Create a new item in ON_SHELF (without Loan)
    data = deepcopy(item_lib_martigny)
    data.pop('barcode')
    data.setdefault('status', ItemStatus.ON_SHELF)
    created_item = Item.create(
        data=data, dbcommit=True, reindex=True, delete_pid=True)

    # Check item is ON_SHELF and NO PENDING loan exist!
    assert created_item.number_of_requests() == 0
    assert created_item.status == ItemStatus.ON_SHELF
    assert not created_item.is_requested_by_patron(
        patron_martigny.get('patron', {}).get('barcode')[0])

    # the following tests the circulation action CHECKOUT_1_1
    # an ON_SHELF item
    # WITHOUT pending loan
    # CAN be CHECKOUT
    params = {
        'patron_pid': patron_martigny.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid,
        'pickup_location_pid': loc_public_martigny.pid
    }
    onloan_item, actions = created_item.checkout(**params)
    loan = Loan.get_record_by_pid(actions[LoanAction.CHECKOUT].get('pid'))
    # Check loan is ITEM_ON_LOAN and item is ON_LOAN
    assert onloan_item.number_of_requests() == 0
    assert onloan_item.status == ItemStatus.ON_LOAN
    assert loan['state'] == LoanState.ITEM_ON_LOAN

    # Fetch a PENDING item and loan
    pending_item, patron, loan = item_on_shelf_martigny_patron_and_loan_pending

    # the following tests the circulation action CHECKOUT_1_2_2
    # an ON_SHELF item
    # WITH pending loan
    # checkout patron != patron of first PENDING loan
    # can NOT be CHECKOUT
    params['patron_pid'] = patron2_martigny.pid
    # CHECKOUT patron is DIFFERENT from 1st PENDING LOAN patron
    assert params['patron_pid'] != patron['pid']
    with pytest.raises(ItemNotAvailableError):
        asked_item, actions = pending_item.checkout(**params)
    checkout_loan = Loan.get_record_by_pid(loan['pid'])
    asked_item = Item.get_record_by_pid(pending_item.pid)
    # Check loan is PENDING and item is ON_SHELF
    assert asked_item.status == ItemStatus.ON_SHELF
    assert checkout_loan['state'] == LoanState.PENDING
    assert asked_item.number_of_requests() == 1

    # the following tests the circulation action CHECKOUT_1_2_1
    # an ON_SHELF item
    # WITH a pending loan
    # checkout patron = patron of first PENDING loan
    # CAN be CHECKOUT
    assert pending_item.is_requested_by_patron(
        patron.patron.get('barcode')[0])
    # Checkout it! CHECKOUT patron == 1st PENDING LOAN patron
    assert patron.get('pid') == loan.get('patron_pid')
    params['patron_pid'] = patron_martigny.pid
    onloan_item, actions = pending_item.checkout(**params, pid=loan.pid)
    loan = Loan.get_record_by_pid(actions[LoanAction.CHECKOUT].get('pid'))
    # Check loan is ITEM_ON_LOAN and item is ON_LOAN
    assert onloan_item.number_of_requests() == 0
    assert onloan_item.status == ItemStatus.ON_LOAN
    assert loan['state'] == LoanState.ITEM_ON_LOAN


def test_checkout_on_item_at_desk(
        item_at_desk_martigny_patron_and_loan_at_desk,
        patron2_martigny,
        loc_public_martigny,
        librarian_martigny):
    """Test CHECKOUT on an AT_DESK item."""
    # Prepare a new item with ITEM_AT_DESK loan
    atdesk_item, patron, loan = item_at_desk_martigny_patron_and_loan_at_desk
    assert atdesk_item.number_of_requests() == 1

    # the following tests the circulation action CHECKOUT_2_2
    # an AT_DESK item
    # checkout patron != patron of first PENDING loan
    # can NOT be CHECKOUT (raise ItemNotAvailableError)
    params = {
        'patron_pid': patron2_martigny.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid,
        'pickup_location_pid': loc_public_martigny.pid
    }
    assert params['patron_pid'] != loan['patron_pid']
    with pytest.raises(ItemNotAvailableError):
        asked_item, actions = atdesk_item.checkout(**params)

    # Check loan is ITEM_AT_DESK and item is AT_DESK
    checkout_loan = Loan.get_record_by_pid(loan.pid)
    asked_item = Item.get_record_by_pid(atdesk_item.pid)
    assert asked_item.status == ItemStatus.AT_DESK
    assert checkout_loan['state'] == LoanState.ITEM_AT_DESK
    assert asked_item.number_of_requests() == 1

    # the following tests the circulation action CHECKOUT_2_1
    # an AT_DESK item
    # checkout patron = patron of first PENDING loan
    # CAN be CHECKOUT
    params.update({'patron_pid': patron['pid']})
    # Checkout it! CHECKOUT patron == 1st PENDING LOAN patron
    assert params['patron_pid'] == loan['patron_pid']
    asked_item, actions = atdesk_item.checkout(**params)
    checkout_loan = Loan.get_record_by_pid(
        actions[LoanAction.CHECKOUT].get('pid'))
    # Check loan is ITEM_ON_LOAN and item is ON_LOAN
    assert asked_item.number_of_requests() == 0
    assert asked_item.status == ItemStatus.ON_LOAN
    assert checkout_loan['state'] == LoanState.ITEM_ON_LOAN


def test_checkout_on_item_on_loan(
        item_on_loan_martigny_patron_and_loan_on_loan,
        patron_martigny,
        patron2_martigny,
        loc_public_martigny,
        librarian_martigny):
    """Test CHECKOUT on an ON_LOAN item."""
    # Prepare a new item with an ITEM_ON_LOAN loan
    onloan_item, patron, loan = item_on_loan_martigny_patron_and_loan_on_loan
    assert onloan_item.number_of_requests() == 0

    # the following tests the circulation action CHECKOUT_3_1
    # an ON_LOAN item
    # checkout patron = patron of current loan
    # can NOT be CHECKOUT
    params = {
        'patron_pid': patron_martigny.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid,
        'pickup_location_pid': loc_public_martigny.pid
    }
    # Checkout it! CHECKOUT patron == current LOAN patron
    assert params['patron_pid'] == patron['pid']
    with pytest.raises(NoValidTransitionAvailableError):
        asked_item, actions = onloan_item.checkout(**params, pid=loan.pid)
    # Check item is ON_SHELF (because no
    # other request + item_member = transaction one)
    checkout_loan = Loan.get_record_by_pid(loan.pid)
    asked_item = Item.get_record_by_pid(onloan_item.pid)
    assert asked_item.status == ItemStatus.ON_LOAN
    assert checkout_loan['state'] == LoanState.ITEM_ON_LOAN

    # the following tests the circulation action CHECKOUT_3_2
    # an ON_LOAN item
    # checkout patron != patron of current loan
    # can NOT be CHECKOUT
    params['patron_pid'] = patron2_martigny.pid
    assert params['patron_pid'] != patron['pid']
    with pytest.raises(ItemNotAvailableError):
        asked_item, actions = onloan_item.checkout(**params)
    asked_item = Item.get_record_by_pid(onloan_item.pid)
    checkout_loan = Loan.get_record_by_pid(loan.pid)
    assert asked_item.status == ItemStatus.ON_LOAN
    assert checkout_loan['state'] == LoanState.ITEM_ON_LOAN
    assert asked_item.number_of_requests() == 0


def test_checkout_on_item_in_transit_for_pickup(
        item_in_transit_martigny_patron_and_loan_for_pickup,
        patron_martigny,
        patron2_martigny,
        loc_public_martigny,
        librarian_martigny, loc_public_saxon):
    """Test CHECKOUT on an IN_TRANSIT (for pickup) item."""
    # Prepare a new item with an IN_TRANSIT loan
    intransit_item, patron, loan = \
        item_in_transit_martigny_patron_and_loan_for_pickup
    assert intransit_item.number_of_requests() == 1

    # the following tests the circulation action CHECKOUT_4_2
    # an IN_TRANSIT (for pickup) item
    # checkout patron != patron of current loan
    # can NOT be CHECKOUT
    params = {
        'patron_pid': patron2_martigny.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid,
        'pickup_location_pid': loc_public_saxon.pid
    }
    assert params['patron_pid'] != patron['pid']
    with pytest.raises(ItemNotAvailableError):
        asked_item, actions = intransit_item.checkout(**params)
    # Check item is ON_LOAN and loan is ITEM_ON_LOAN
    asked_item = Item.get_record_by_pid(intransit_item.pid)
    checkout_loan = Loan.get_record_by_pid(loan.pid)
    assert asked_item.status == ItemStatus.IN_TRANSIT
    assert checkout_loan['state'] == LoanState.ITEM_IN_TRANSIT_FOR_PICKUP

    # the following tests the circulation action CHECKOUT_4_1
    # an IN_TRANSIT (for pickup) item
    # checkout patron = patron of current loan
    # CAN be CHECKOUT
    params['patron_pid'] = patron_martigny.pid
    # Checkout it! CHECKOUT patron == current LOAN patron
    assert params['patron_pid'] == patron['pid']
    asked_item, actions = intransit_item.checkout(**params, pid=loan.pid)
    checkout_loan = Loan.get_record_by_pid(
        actions[LoanAction.CHECKOUT].get('pid'))
    # Check item is ON_LOAN and loan is ITEM_ON_LOAN
    assert asked_item.status == ItemStatus.ON_LOAN
    assert checkout_loan['state'] == LoanState.ITEM_ON_LOAN


def test_checkout_on_item_in_transit_to_house(
        item_in_transit_martigny_patron_and_loan_to_house,
        patron_martigny,
        librarian_martigny,
        loc_public_martigny,
        loc_public_saxon):
    """Test CHECKOUT on an IN_TRANSIT (to house) item."""
    # Create a new item in IN_TRANSIT_TO_HOUSE
    intransit_item, patron, loan = \
        item_in_transit_martigny_patron_and_loan_to_house
    assert intransit_item.number_of_requests() == 0

    # the following tests the circulation action CHECKOUT_5_1
    # an IN_TRANSIT (to house) item
    # WITHOUT pending loan
    # CAN be CHECKOUT
    params = {
        'patron_pid': patron_martigny.pid,
        'transaction_location_pid': loc_public_saxon.pid,
        'transaction_user_pid': librarian_martigny.pid,
        'pickup_location_pid': loc_public_martigny.pid,
    }
    # Checkout it!
    asked_item, actions = intransit_item.checkout(**params, pid=loan.pid)
    checkout_loan = Loan.get_record_by_pid(
        actions[LoanAction.CHECKOUT].get('pid'))
    # Check loan is ITEM_ON_LOAN and item is ON_LOAN
    assert intransit_item.status == ItemStatus.ON_LOAN
    assert checkout_loan['state'] == LoanState.ITEM_ON_LOAN
    assert intransit_item.number_of_requests() == 0


def test_checkout_on_item_in_transit_to_house_for_another_patron(
        item2_in_transit_martigny_patron_and_loan_to_house,
        patron2_martigny,
        librarian_martigny,
        loc_public_martigny,
        loc_public_saxon):
    """Test CHECKOUT on an IN_TRANSIT (to house) item."""
    # Create a new item in IN_TRANSIT_TO_HOUSE
    intransit_item, patron, loan = \
        item2_in_transit_martigny_patron_and_loan_to_house
    assert intransit_item.number_of_requests() == 0

    # the following tests the circulation action CHECKOUT_5_1
    # an IN_TRANSIT (to house) item
    # WITHOUT pending loan
    # CAN be CHECKOUT
    params = {
        'patron_pid': patron2_martigny.pid,
        'transaction_location_pid': loc_public_saxon.pid,
        'transaction_user_pid': librarian_martigny.pid,
        'pickup_location_pid': loc_public_martigny.pid,
    }
    # Checkout it!
    asked_item, actions = intransit_item.checkout(**params, pid=loan.pid)
    checkout_loan = Loan.get_record_by_pid(
        actions[LoanAction.CHECKOUT].get('pid'))
    # Check loan is ITEM_ON_LOAN and item is ON_LOAN
    assert intransit_item.status == ItemStatus.ON_LOAN
    assert checkout_loan['state'] == LoanState.ITEM_ON_LOAN
    assert intransit_item.number_of_requests() == 0


def test_checkout_on_item_in_transit_to_house_with_pending_loan(
        item_in_transit_martigny_patron_and_loan_to_house,
        item_lib_martigny,
        patron2_martigny,
        loc_public_martigny,
        librarian_martigny,
        loc_public_fully):
    """Test item IN_TRANSIT (to house), WITHOUT pending loan, same patron."""
    # Create a new item in IN_TRANSIT_TO_HOUSE
    intransit_item, patron, loan = \
        item_in_transit_martigny_patron_and_loan_to_house
    assert intransit_item.number_of_requests() == 0

    params = {
        'patron_pid': patron['pid'],
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid,
        'pickup_location_pid': loc_public_martigny.pid,
        'checkin_transaction_location_pid': loc_public_fully.pid
    }
    # WARNING: this test works alone. But with other test, we need to check
    # if item is ON_LOAN. If yes: create a new item and loan
    if intransit_item.status == ItemStatus.ON_LOAN:
        intransit_item, loan = item_record_to_a_specific_loan_state(
            item=item_lib_martigny,
            loan_state=LoanState.ITEM_IN_TRANSIT_TO_HOUSE,
            params=params)

    # Create a pending loan
    params['patron_pid'] = patron2_martigny.pid
    checked_item, requested_loan = item_record_to_a_specific_loan_state(
        item=intransit_item,
        loan_state=LoanState.PENDING,
        params=params,
        copy_item=False)
    assert loan['state'] == LoanState.ITEM_IN_TRANSIT_TO_HOUSE
    assert requested_loan['state'] == LoanState.PENDING
    assert checked_item.number_of_requests() == 1

    # the following tests the circulation action CHECKOUT_5_2_2
    # an IN_TRANSIT (to house) item
    # WITH pending loan
    # checkout patron != patron of first pending loan
    # can NOT be CHECKOUT
    params['patron_pid'] = patron['pid']
    assert params['patron_pid'] != requested_loan.patron_pid
    assert intransit_item.status == ItemStatus.IN_TRANSIT
    assert loan['state'] == LoanState.ITEM_IN_TRANSIT_TO_HOUSE
    with pytest.raises(TransitionConstraintsViolationError):
        asked_item, actions = intransit_item.checkout(
            **params, pid=requested_loan.pid)
    asked_item = Item.get_record_by_pid(intransit_item.pid)
    checkout_loan = Loan.get_record_by_pid(loan.pid)
    assert asked_item.status == ItemStatus.IN_TRANSIT
    assert checkout_loan['state'] == LoanState.ITEM_IN_TRANSIT_TO_HOUSE

    # the following tests the circulation action CHECKOUT_5_2_1
    # an IN_TRANSIT (to house) item
    # WITH pending loan
    # checkout patron = patron of first pending loan
    # CAN BE CHECKOUT
    # Checkout it! CHECKOUT patron = patron of first PENDING loan
    assert params['patron_pid'] == loan.patron_pid
    assert intransit_item.status == ItemStatus.IN_TRANSIT
    assert loan['state'] == LoanState.ITEM_IN_TRANSIT_TO_HOUSE
    # What differs from CHECKOUT_5_2_2 is the given LOAN (`pid=`)
    checkout_item, actions = asked_item.checkout(**params, pid=loan.pid)
    checkout_loan = Loan.get_record_by_pid(
        actions[LoanAction.CHECKOUT].get('pid'))
    # Check loan is ITEM_ON_LOAN and item is ON_LOAN
    assert checkout_item.status == ItemStatus.ON_LOAN
    assert checkout_loan['state'] == LoanState.ITEM_ON_LOAN
    assert checkout_item.number_of_requests() == 1  # pending loan remains
