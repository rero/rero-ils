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

"""Test item circulation extend actions."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone

import ciso8601
import pytest
from invenio_circulation.errors import CirculationException
from utils import flush_index, item_record_to_a_specific_loan_state

from rero_ils.modules.circ_policies.api import CircPolicy
from rero_ils.modules.errors import NoCirculationAction
from rero_ils.modules.items.models import ItemStatus
from rero_ils.modules.libraries.api import Library
from rero_ils.modules.loans.api import Loan
from rero_ils.modules.loans.models import LoanAction, LoanState
from rero_ils.modules.loans.utils import get_circ_policy
from rero_ils.modules.patron_transactions.api import PatronTransactionsSearch
from rero_ils.modules.patron_transactions.utils import \
    get_last_transaction_by_loan_pid
from rero_ils.modules.utils import get_ref_for_pid


def test_fees_after_extend(
    item_on_loan_martigny_patron_and_loan_on_loan,
    loc_public_martigny, loc_public_saxon, librarian_martigny,
    circulation_policies
):
    """Test fees calculation after extend on different location."""

    # STEP#1 :: CREATE A SPECIAL CIPO FOR NEXT EXTEND OPERATION
    item, patron, loan = item_on_loan_martigny_patron_and_loan_on_loan
    checkout_cipo = get_circ_policy(loan)
    extend_cipo = deepcopy(checkout_cipo)
    extend_cipo['policy_library_level'] = True
    extend_cipo.update({
        'libraries': [
            {'$ref': get_ref_for_pid(Library, loc_public_saxon.library_pid)}
        ],
        'overdue_fees': {
            'intervals': [{'from': 1, 'fee_amount': 0.01}]
        }
    })
    del extend_cipo['pid']
    extend_cipo = CircPolicy.create(extend_cipo)
    assert extend_cipo

    # Update checkout cipo to set some intervals
    checkout_cipo_ori = get_circ_policy(loan, checkout_location=True)
    checkout_cipo = deepcopy(checkout_cipo_ori)
    checkout_fee_amount = 10
    checkout_cipo['overdue_fees'] = {
        'intervals': [{'from': 1, 'fee_amount': checkout_fee_amount}]
    }
    checkout_cipo = checkout_cipo.update(
        checkout_cipo, dbcommit=True, reindex=True)

    # UPDATE LOAN TO BE OVERDUE
    # LIBRARY FIXTURES EXCEPTION: Christmas Holidays is 15 days
    interval = 20
    while not loan.is_loan_overdue():
        new_end_date = datetime.now(timezone.utc) - timedelta(days=interval)
        loan['end_date'] = new_end_date.isoformat()
        interval += 1
    loan.update(loan, dbcommit=True, reindex=True)

    # STEP#2 :: EXTEND THE LOAN FOR SAXON LIBRARY.
    #   The loan should use the new created circulation policy
    #   Update loan `end_date` to play with "extend" function without problem
    params = {
        'transaction_location_pid': loc_public_saxon.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    item, actions = item.extend_loan(**params)
    loan = actions[LoanAction.EXTEND]
    assert item.status == ItemStatus.ON_LOAN
    assert get_circ_policy(loan).pid == extend_cipo.pid
    assert loan.get('checkout_location_pid') == loc_public_martigny.pid
    assert loan.get('transaction_location_pid') == loc_public_saxon.pid

    # The patron should have fees.
    flush_index(PatronTransactionsSearch.Meta.index)
    pttr = get_last_transaction_by_loan_pid(loan.pid)
    assert pttr.total_amount >= checkout_fee_amount

    # UPDATE LOAN TO BE OVERDUE
    interval = 10
    while not loan.is_loan_overdue():
        new_end_date = datetime.now(timezone.utc) - timedelta(days=interval)
        loan['end_date'] = new_end_date.isoformat()
        interval += 1
    loan.update(loan, dbcommit=True, reindex=True)

    # STEP#3 :: CHECK-IN THE LOAN
    #   Execute the check-in circulation operation
    #   Check that a fee has been created and this fees is related to the
    #   checkout circulation.
    params = {
        'transaction_location_pid': loc_public_saxon.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    _, actions = item.checkin(**params)
    loan = actions[LoanAction.CHECKIN]
    assert loan.state == LoanState.ITEM_IN_TRANSIT_TO_HOUSE
    params['transaction_location_pid'] = loc_public_martigny.pid
    _, actions = item.checkin(**params)
    loan = actions[LoanAction.RECEIVE]
    assert loan.state == LoanState.ITEM_RETURNED

    pttr = get_last_transaction_by_loan_pid(loan.pid)
    assert pttr.total_amount >= checkout_fee_amount

    # STEP#X :: RESET DATA
    checkout_cipo.update(checkout_cipo_ori, dbcommit=True, reindex=True)
    extend_cipo.delete()


def test_extend_on_item_on_shelf(
        item_lib_martigny, patron_martigny,
        loc_public_martigny, librarian_martigny,
        circulation_policies):
    """Test extend an on_shelf item."""
    # the following tests the circulation action EXTEND_1
    # for an on_shelf item, the extend action is not possible.

    params = {
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    with pytest.raises(NoCirculationAction):
        item, actions = item_lib_martigny.extend_loan(**params)
    assert item_lib_martigny.status == ItemStatus.ON_SHELF


def test_extend_on_item_at_desk(
        item_at_desk_martigny_patron_and_loan_at_desk,
        loc_public_martigny, librarian_martigny,
        circulation_policies):
    """Test extend an at_desk item."""
    # the following tests the circulation action EXTEND_2
    # for an at_desk item, the extend action is not possible.
    item, patron, loan = item_at_desk_martigny_patron_and_loan_at_desk
    # test fails if no loan pid is given
    params = {
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    with pytest.raises(NoCirculationAction):
        item, actions = item.extend_loan(**params)
    assert item.status == ItemStatus.AT_DESK
    params = {
        'pid': loan.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    with pytest.raises(CirculationException):
        item, actions = item.extend_loan(**params)
    assert item.status == ItemStatus.AT_DESK


def test_extend_on_item_on_loan_with_no_requests(
        app, item_on_loan_martigny_patron_and_loan_on_loan,
        loc_public_martigny, librarian_martigny, lib_martigny,
        circulation_policies):
    """Test extend an on_loan item."""
    # the following tests the circulation action EXTEND_3_1
    # for an on_loan item with no requests, the extend action is possible.
    item, patron, loan = item_on_loan_martigny_patron_and_loan_on_loan
    settings = deepcopy(app.config['CIRCULATION_POLICIES']['extension'])
    cipo = get_circ_policy(loan)

    # FIRST TEST :: Extends expected from loan 'end_date'
    #   The loan will be extended by 'extension_duration' days from related
    #   circulation policies excepting if some closed date exist for the
    #   related library. As the checkout already set the 'end_date' to the end
    #   of day, no timedelta should appears on hour/min/sec new end_date
    app.config['CIRCULATION_POLICIES']['extension']['from_end_date'] = True
    # Update loan `end_date` to play with "extend" function without problem
    end_date = ciso8601.parse_datetime(str(loan.get('end_date')))
    start_date = ciso8601.parse_datetime(str(loan.get('start_date')))
    end_date = end_date.replace(
        year=start_date.year,
        month=start_date.month,
        day=start_date.day
    )
    loan['end_date'] = end_date.isoformat()
    start_date = datetime.now() - timedelta(days=cipo['checkout_duration'])
    loan['start_date'] = start_date.isoformat()
    loan['transaction_date'] = start_date.isoformat()
    initial_loan_data = deepcopy(loan)
    initial_loan = loan.update(loan, dbcommit=True, reindex=True)
    # Extend the loan
    params = {
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    item, actions = item.extend_loan(**params)
    assert item.status == ItemStatus.ON_LOAN
    extended_loan = Loan.get_record_by_pid(initial_loan.pid)

    init_end_date = ciso8601.parse_datetime(str(initial_loan.end_date))
    expected_date = init_end_date + timedelta(days=cipo['renewal_duration'])
    expected_date_eve = expected_date - timedelta(days=1)
    expected_date = lib_martigny.next_open(expected_date_eve)

    ext_end_date = ciso8601.parse_datetime(str(extended_loan.end_date))
    assert expected_date.strftime('%Y%m%d') == ext_end_date.strftime('%Y%m%d')

    # SECOND TEST :: Extends expected from loan `transaction_date`
    #   The loan will also be extended from 'extension_duration' days excepting
    #   library possible closed dates. But new end_date time should always
    #   match end_of_the_day regardless the transaction_date.

    app.config['CIRCULATION_POLICIES']['extension']['from_end_date'] = False
    initial_loan = loan.update(initial_loan_data, dbcommit=True, reindex=True)
    # Extend the loan
    params = {
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    item, actions = item.extend_loan(**params)
    assert item.status == ItemStatus.ON_LOAN
    extended_loan = Loan.get_record_by_pid(initial_loan.pid)

    expected_date = datetime.now() + timedelta(days=cipo['renewal_duration'])
    expected_date_eve = expected_date - timedelta(days=1)
    expected_date = lib_martigny.next_open(expected_date_eve)

    ext_end_date = ciso8601.parse_datetime(str(extended_loan.end_date))
    assert expected_date.strftime('%Y%m%d') == ext_end_date.strftime('%Y%m%d')

    # Reset the application configuration
    app.config['CIRCULATION_POLICIES']['extension'] = settings


def test_extend_on_item_on_loan_with_requests(
        item_on_loan_martigny_patron_and_loan_on_loan,
        loc_public_martigny, librarian_martigny,
        circulation_policies, patron2_martigny):
    """Test extend an on_loan item with requests."""
    # the following tests the circulation action EXTEND_3_2
    # for an on_loan item with requests, the extend action is not possible.
    item, patron, loan = item_on_loan_martigny_patron_and_loan_on_loan

    params = {
        'patron_pid': patron2_martigny.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid,
        'pickup_location_pid': loc_public_martigny.pid
    }
    item, requested_loan = item_record_to_a_specific_loan_state(
        item=item, loan_state=LoanState.PENDING, params=params,
        copy_item=False)
    # test fails if no loan pid is given
    params = {
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    with pytest.raises(NoCirculationAction):
        item, actions = item.extend_loan(**params)
    assert item.status == ItemStatus.ON_LOAN
    # test fails if loan pid is given
    params = {
        'pid': loan.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    with pytest.raises(NoCirculationAction):
        item, actions = item.extend_loan(**params)
    assert item.status == ItemStatus.ON_LOAN


def test_extend_on_item_in_transit_for_pickup(
        item_in_transit_martigny_patron_and_loan_for_pickup,
        loc_public_martigny, librarian_martigny,
        circulation_policies):
    """Test extend an in_transit for pickup item."""
    # the following tests the circulation action EXTEND_4
    # for an in_transit item, the extend action is not possible.
    item, patron, loan = item_in_transit_martigny_patron_and_loan_for_pickup
    # test fails if no loan pid is given
    params = {
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    with pytest.raises(NoCirculationAction):
        item, actions = item.extend_loan(**params)
    assert item.status == ItemStatus.IN_TRANSIT
    # test fails if a loan pid is given
    params = {
        'pid': loan.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    with pytest.raises(CirculationException):
        item, actions = item.extend_loan(**params)
    assert item.status == ItemStatus.IN_TRANSIT


def test_extend_on_item_in_transit_to_house(
        item_in_transit_martigny_patron_and_loan_to_house,
        loc_public_martigny, librarian_martigny,
        circulation_policies):
    """Test extend an in_transit to_house item."""
    # the following tests the circulation action EXTEND_4
    # for an in_transit item, the extend action is not possible.
    item, patron, loan = item_in_transit_martigny_patron_and_loan_to_house
    # test fails if no loan pid is given
    params = {
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    with pytest.raises(NoCirculationAction):
        item, actions = item.extend_loan(**params)
    assert item.status == ItemStatus.IN_TRANSIT
    # test fails if a loan pid is given
    params = {
        'pid': loan.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    with pytest.raises(CirculationException):
        item, actions = item.extend_loan(**params)
    assert item.status == ItemStatus.IN_TRANSIT
