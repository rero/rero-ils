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

"""Test item circulation request actions."""


import pytest
from invenio_circulation.errors import RecordCannotBeRequestedError
from utils import item_record_to_a_specific_loan_state

from rero_ils.modules.items.models import ItemStatus
from rero_ils.modules.loans.api import LoanState


def test_add_request_1_actions(client, librarian_martigny_no_email,
                               item_lib_martigny, loc_public_martigny,
                               patron_martigny_no_email, circulation_policies,
                               patron2_martigny_no_email):
    """Test add request_1 actions"""
    # test add_request_1_1 action
    # item on_shelf (no current loan): PENDING loan does not exist
    params = {
        'patron_pid': patron_martigny_no_email.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny_no_email.pid,
        'pickup_location_pid': loc_public_martigny.pid
    }

    item, loan = item_record_to_a_specific_loan_state(
        item=item_lib_martigny, loan_state=LoanState.PENDING, params=params,
        copy_item=True)

    assert item.number_of_requests() == 1
    assert item.status == ItemStatus.ON_SHELF
    assert item.is_requested_by_patron(
        patron_martigny_no_email.get('barcode'))
    assert loan.get('state') == LoanState.PENDING

    # test add_request_1_2 action: PENDING loan exists
    # add_request_1_2_1: request patron = current loan patron (request denied)
    with pytest.raises(RecordCannotBeRequestedError):
        item, loan = item_record_to_a_specific_loan_state(
            item=item, loan_state=LoanState.PENDING, params=params,
            copy_item=False)

    assert item.status == ItemStatus.ON_SHELF
    assert item.number_of_requests() == 1
    # add_request_1_2_2: request patron != current loan patron (to PENDING)
    params['patron_pid'] = patron2_martigny_no_email.pid
    item, loan = item_record_to_a_specific_loan_state(
        item=item, loan_state=LoanState.PENDING, params=params,
        copy_item=False)

    assert item.status == ItemStatus.ON_SHELF
    assert item.number_of_requests() == 2
    assert item.is_requested_by_patron(
        patron2_martigny_no_email.get('barcode'))
    assert loan.get('state') == LoanState.PENDING


def test_add_request_2_actions(client, librarian_martigny_no_email,
                               item_lib_martigny, loc_public_martigny,
                               patron_martigny_no_email, circulation_policies,
                               patron2_martigny_no_email):
    """Test add request_2 actions"""

    # ADD_REQUEST_2: item at_desk, requested (ITEM_AT_DESK)
    params = {
        'patron_pid': patron_martigny_no_email.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny_no_email.pid,
        'pickup_location_pid': loc_public_martigny.pid
    }

    item, loan = item_record_to_a_specific_loan_state(
        item=item_lib_martigny, loan_state=LoanState.ITEM_AT_DESK,
        params=params, copy_item=True)

    assert item.number_of_requests() == 1
    assert item.status == ItemStatus.AT_DESK
    assert loan.get('state') == LoanState.ITEM_AT_DESK
    # request patron = current loan patron -> request denied
    with pytest.raises(RecordCannotBeRequestedError):
        item, loan = item_record_to_a_specific_loan_state(
            item=item, loan_state=LoanState.PENDING,
            params=params, copy_item=False)
    assert item.status == ItemStatus.AT_DESK
    assert loan.get('state') == LoanState.ITEM_AT_DESK

    # request patron != current loan patron (add loan PENDING)
    params['patron_pid'] = patron2_martigny_no_email.pid
    item, requested_loan = item_record_to_a_specific_loan_state(
        item=item, loan_state=LoanState.PENDING, params=params,
        copy_item=False)
    assert item.is_requested_by_patron(
        patron2_martigny_no_email.get('barcode'))
    assert item.is_requested_by_patron(
        patron_martigny_no_email.get('barcode'))
    assert requested_loan.get('state') == LoanState.PENDING
    assert item.status == ItemStatus.AT_DESK
    assert loan.get('state') == LoanState.ITEM_AT_DESK


def test_add_request_3_actions(client, librarian_martigny_no_email,
                               item_lib_martigny, loc_public_martigny,
                               patron_martigny_no_email, circulation_policies,
                               patron2_martigny_no_email,
                               patron4_martigny_no_email):
    """Test add request_3 actions"""

    # ADD_REQUEST_3: item on_loan (ITEM_ON_LOAN)
    params = {
        'patron_pid': patron_martigny_no_email.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny_no_email.pid,
        'pickup_location_pid': loc_public_martigny.pid
    }

    item, loan = item_record_to_a_specific_loan_state(
        item=item_lib_martigny, loan_state=LoanState.ITEM_ON_LOAN,
        params=params, copy_item=True)

    assert item.number_of_requests() == 0
    assert item.status == ItemStatus.ON_LOAN
    assert loan.get('state') == LoanState.ITEM_ON_LOAN
    # 3_1: request patron = current loan patron -> request denied
    with pytest.raises(RecordCannotBeRequestedError):
        item, loan = item_record_to_a_specific_loan_state(
            item=item, loan_state=LoanState.PENDING,
            params=params, copy_item=False)
    assert item.status == ItemStatus.ON_LOAN
    assert loan.get('state') == LoanState.ITEM_ON_LOAN

    # 3_2: request patron != current loan patron:
    # 3_2_1: PENDING loan does not exist -> (add loan PENDING)
    params['patron_pid'] = patron2_martigny_no_email.pid
    item, requested_loan = item_record_to_a_specific_loan_state(
        item=item, loan_state=LoanState.PENDING, params=params,
        copy_item=False)
    assert item.is_requested_by_patron(
        patron2_martigny_no_email.get('barcode'))
    assert requested_loan.get('state') == LoanState.PENDING
    assert item.status == ItemStatus.ON_LOAN
    assert loan.get('state') == LoanState.ITEM_ON_LOAN

    # 3_2_2: PENDING loan exists
    # 3_2_2_1: request patron = PENDING loan patron -> request denied
    params['patron_pid'] = patron2_martigny_no_email.pid
    with pytest.raises(RecordCannotBeRequestedError):
        item, loan = item_record_to_a_specific_loan_state(
            item=item, loan_state=LoanState.PENDING,
            params=params, copy_item=False)
    assert item.status == ItemStatus.ON_LOAN
    assert loan.get('state') == LoanState.ITEM_ON_LOAN

    # 3_2_2_2: request patron != PENDING loan patron -> (add loan PENDING)
    params['patron_pid'] = patron4_martigny_no_email.pid
    item, second_requested_loan = item_record_to_a_specific_loan_state(
        item=item, loan_state=LoanState.PENDING, params=params,
        copy_item=False)
    assert item.is_requested_by_patron(
        patron4_martigny_no_email.get('barcode'))
    assert requested_loan.get('state') == LoanState.PENDING
    assert second_requested_loan.get('state') == LoanState.PENDING
    assert item.status == ItemStatus.ON_LOAN
    assert loan.get('state') == LoanState.ITEM_ON_LOAN


def test_add_request_4_actions(client, librarian_martigny_no_email,
                               item_lib_martigny, loc_public_martigny,
                               patron_martigny_no_email, circulation_policies,
                               patron2_martigny_no_email,
                               patron4_martigny_no_email, loc_public_fully):
    """Test add request_4 actions"""

    # ADD_REQUEST_4: item in_transit (IN_TRANSIT_FOR_PICKUP)
    params = {
        'patron_pid': patron_martigny_no_email.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny_no_email.pid,
        'pickup_location_pid': loc_public_fully.pid
    }

    item, loan = item_record_to_a_specific_loan_state(
        item=item_lib_martigny,
        loan_state=LoanState.ITEM_IN_TRANSIT_FOR_PICKUP,
        params=params, copy_item=True)

    assert item.number_of_requests() == 1
    assert item.status == ItemStatus.IN_TRANSIT
    assert loan.get('state') == LoanState.ITEM_IN_TRANSIT_FOR_PICKUP

    # 4_1: request patron = current loan patron -> request denied
    with pytest.raises(RecordCannotBeRequestedError):
        item, loan = item_record_to_a_specific_loan_state(
            item=item, loan_state=LoanState.PENDING,
            params=params, copy_item=False)
    assert item.status == ItemStatus.IN_TRANSIT
    assert loan.get('state') == LoanState.ITEM_IN_TRANSIT_FOR_PICKUP

    # 4_2: request patron != current loan patron -> (add loan PENDING)
    params['patron_pid'] = patron2_martigny_no_email.pid
    item, requested_loan = item_record_to_a_specific_loan_state(
        item=item, loan_state=LoanState.PENDING, params=params,
        copy_item=False)
    assert item.is_requested_by_patron(
        patron2_martigny_no_email.get('barcode'))
    assert requested_loan.get('state') == LoanState.PENDING
    assert item.status == ItemStatus.IN_TRANSIT
    assert loan.get('state') == LoanState.ITEM_IN_TRANSIT_FOR_PICKUP


def test_add_request_5_actions(client, librarian_martigny_no_email,
                               item_lib_martigny, loc_public_martigny,
                               patron_martigny_no_email, circulation_policies,
                               patron2_martigny_no_email, loc_public_saxon,
                               patron4_martigny_no_email, loc_public_fully):
    """Test add request_4 actions"""

    # ADD_REQUEST_5: item in_transit (ITEM_IN_TRANSIT_TO_HOUSE)
    params = {
        'patron_pid': patron_martigny_no_email.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny_no_email.pid,
        'pickup_location_pid': loc_public_martigny.pid,
        'checkin_transaction_location_pid': loc_public_fully.pid,
    }

    item, loan = item_record_to_a_specific_loan_state(
        item=item_lib_martigny,
        loan_state=LoanState.ITEM_IN_TRANSIT_TO_HOUSE,
        params=params, copy_item=True)

    assert item.number_of_requests() == 0
    assert item.status == ItemStatus.IN_TRANSIT
    assert loan.get('state') == LoanState.ITEM_IN_TRANSIT_TO_HOUSE

    # 5_1: PENDING loan does not exist : add loan PENDING
    params = {
        'patron_pid': patron_martigny_no_email.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny_no_email.pid,
        'pickup_location_pid': loc_public_martigny.pid
    }
    item, requested_loan = item_record_to_a_specific_loan_state(
        item=item, loan_state=LoanState.PENDING, params=params,
        copy_item=False)
    assert item.status == ItemStatus.IN_TRANSIT
    assert loan.get('state') == LoanState.ITEM_IN_TRANSIT_TO_HOUSE
    assert requested_loan.get('state') == LoanState.PENDING

    params = {
        'patron_pid': patron2_martigny_no_email.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny_no_email.pid,
        'pickup_location_pid': loc_public_saxon.pid
    }
    item, requested_2nd_loan = item_record_to_a_specific_loan_state(
        item=item, loan_state=LoanState.PENDING, params=params,
        copy_item=False)
    assert item.status == ItemStatus.IN_TRANSIT
    assert loan.get('state') == LoanState.ITEM_IN_TRANSIT_TO_HOUSE
    assert requested_2nd_loan.get('state') == LoanState.PENDING

    # 5_2: PENDING loan exists
    # 5_2_1: request patron = current loan patron -> request denied
    params = {
        'patron_pid': patron_martigny_no_email.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny_no_email.pid,
        'pickup_location_pid': loc_public_martigny.pid
    }
    with pytest.raises(RecordCannotBeRequestedError):
        item_record_to_a_specific_loan_state(
            item=item, loan_state=LoanState.PENDING, params=params,
            copy_item=False)
    assert item.status == ItemStatus.IN_TRANSIT
    assert loan.get('state') == LoanState.ITEM_IN_TRANSIT_TO_HOUSE
    assert requested_loan.get('state') == LoanState.PENDING

    # 5_2_2: request patron != current loan patron -> (add loan PENDING)
    params = {
        'patron_pid': patron4_martigny_no_email.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny_no_email.pid,
        'pickup_location_pid': loc_public_saxon.pid
    }
    item, requested_3nd_loan = item_record_to_a_specific_loan_state(
        item=item, loan_state=LoanState.PENDING, params=params,
        copy_item=False)
    assert item.status == ItemStatus.IN_TRANSIT
    assert loan.get('state') == LoanState.ITEM_IN_TRANSIT_TO_HOUSE
    assert requested_3nd_loan.get('state') == LoanState.PENDING
