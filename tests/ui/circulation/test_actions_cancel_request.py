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

"""Test item circulation cancel request actions."""


from copy import deepcopy

import pytest
from utils import item_record_to_a_specific_loan_state

from rero_ils.modules.errors import NoCirculationAction
from rero_ils.modules.items.api import Item
from rero_ils.modules.items.models import ItemStatus
from rero_ils.modules.loans.api import Loan
from rero_ils.modules.loans.models import LoanState


def test_cancel_item_request_in_transit_for_pickup_with_requests_same_lib(
        client, item3_in_transit_martigny_patron_and_loan_for_pickup,
        loc_public_martigny, librarian_martigny, librarian_fully,
        loc_public_fully, patron2_martigny):
    """Test cancel requests on an in_transit for pickup item with requests."""
    item, patron, loan = item3_in_transit_martigny_patron_and_loan_for_pickup
    origin_loan = deepcopy(loan)
    # the following tests a special case of the circulation action
    # CANCEL_REQUEST_4_1_2 an item in_transit for pickup with
    # other pending loans and the pickup locations are the same.

    params = {
        'patron_pid': patron2_martigny.pid,
        'transaction_location_pid': loc_public_fully.pid,
        'transaction_user_pid': librarian_fully.pid,
        'pickup_location_pid': loc_public_fully.pid
    }
    item, requested_loan = item_record_to_a_specific_loan_state(
        item=item, loan_state=LoanState.PENDING,
        params=params, copy_item=False)
    assert requested_loan['state'] == LoanState.PENDING

    params = {
        'pid': loan.pid,
        'transaction_location_pid': loc_public_fully.pid,
        'transaction_user_pid': librarian_fully.pid
    }
    item.cancel_item_request(**params)
    item = Item.get_record_by_pid(item.pid)
    loan = Loan.get_record_by_pid(loan.pid)
    requested_loan = Loan.get_record_by_pid(requested_loan.pid)
    assert item.status == ItemStatus.IN_TRANSIT
    assert loan['state'] == LoanState.CANCELLED
    assert requested_loan['state'] == LoanState.ITEM_IN_TRANSIT_FOR_PICKUP

    # Clean created data
    requested_loan.delete(force=True, dbcommit=True, delindex=True)
    loan.replace(origin_loan, True, True, True)
    Item.status_update(item=item, on_shelf=False, dbcommit=True, reindex=True)


def test_cancel_request_on_item_on_shelf(
        item_lib_martigny, item_on_shelf_martigny_patron_and_loan_pending,
        loc_public_martigny, librarian_martigny,
        patron2_martigny):
    """Test cancel request on an on_shelf item."""
    # the following tests the circulation action CANCEL_REQUEST_1_1
    # on_shelf item with no pending requests, not possible to cancel a request.
    # a loan pid is a required parameter and not given
    with pytest.raises(TypeError):
        item_lib_martigny.cancel_item_request()
    assert item_lib_martigny.status == ItemStatus.ON_SHELF

    # the following tests the circulation action CANCEL_REQUEST_1_2
    # on_shelf item with pending requests, cancel a pending loan is possible.
    # the item remains on_shelf
    item, patron, loan = item_on_shelf_martigny_patron_and_loan_pending
    # add request for another patron
    params = {
        'patron_pid': patron2_martigny.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid,
        'pickup_location_pid': loc_public_martigny.pid
    }
    item, requested_loan = item_record_to_a_specific_loan_state(
        item=item, loan_state=LoanState.PENDING,
        params=params, copy_item=False)
    # cancel request
    params = {
        'pid': loan.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    item.cancel_item_request(**params)
    item = Item.get_record_by_pid(item.pid)
    loan = Loan.get_record_by_pid(loan.pid)
    assert item.status == ItemStatus.ON_SHELF
    assert loan['state'] == LoanState.CANCELLED


def test_cancel_request_on_item_at_desk_no_requests_externally(
        client, item_at_desk_martigny_patron_and_loan_at_desk,
        loc_public_martigny, librarian_martigny,
        loc_public_fully):
    """Test cancel requests on an at_desk item externally."""
    item, patron, loan = item_at_desk_martigny_patron_and_loan_at_desk
    # the following tests the circulation action CANCEL_REQUEST_2_1_1_1
    # an item at_desk with no other pending loans.
    # if the item library != pickup location, update the at_desk loan.
    # loan ITEM_IN_TRANSIT_TO_HOUSE and item is: in_transit
    params = {
        'pid': loan.pid,
        'transaction_location_pid': loc_public_fully.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    item.cancel_item_request(**params)
    item = Item.get_record_by_pid(item.pid)
    loan = Loan.get_record_by_pid(loan.pid)
    assert item.status == ItemStatus.IN_TRANSIT
    assert loan['state'] == LoanState.ITEM_IN_TRANSIT_TO_HOUSE


def test_cancel_request_on_item_at_desk_no_requests_at_home(
        client, item2_at_desk_martigny_patron_and_loan_at_desk,
        loc_public_martigny, librarian_martigny):
    """Test cancel requests on an at_desk item at home."""
    item, patron, loan = item2_at_desk_martigny_patron_and_loan_at_desk
    # the following tests the circulation action CANCEL_REQUEST_2_1_1_2
    # an item at_desk with no other pending loans.
    # if the item library = pickup location, cancels the
    # loan and item is: on_shelf
    params = {
        'pid': loan.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    item.cancel_item_request(**params)
    item = Item.get_record_by_pid(item.pid)
    loan = Loan.get_record_by_pid(loan.pid)
    assert item.status == ItemStatus.ON_SHELF
    assert loan['state'] == LoanState.CANCELLED


def test_cancel_request_on_item_at_desk_with_requests_externally(
        client, item3_at_desk_martigny_patron_and_loan_at_desk,
        loc_public_martigny, librarian_martigny,
        patron2_martigny, loc_public_fully):
    """Test cancel requests on an at_desk item with requests at externally."""
    item, patron, loan = item3_at_desk_martigny_patron_and_loan_at_desk
    # the following tests the circulation action CANCEL_REQUEST_2_1_2_1
    # an item at_desk with other pending loans.
    # pickup location of 1st pending loan != pickup location of current loan
    # cancel the current loan and item is: in_transit, automatic validation of
    # firt pending loan

    params = {
        'patron_pid': patron2_martigny.pid,
        'transaction_location_pid': loc_public_fully.pid,
        'transaction_user_pid': librarian_martigny.pid,
        'pickup_location_pid': loc_public_fully.pid
    }
    item, requested_loan = item_record_to_a_specific_loan_state(
        item=item, loan_state=LoanState.PENDING,
        params=params, copy_item=False)
    assert requested_loan['state'] == LoanState.PENDING

    params = {
        'pid': loan.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    item.cancel_item_request(**params)
    item = Item.get_record_by_pid(item.pid)
    loan = Loan.get_record_by_pid(loan.pid)
    requested_loan = Loan.get_record_by_pid(requested_loan.pid)
    assert item.status == ItemStatus.IN_TRANSIT
    assert loan['state'] == LoanState.CANCELLED
    assert requested_loan['state'] == LoanState.ITEM_IN_TRANSIT_FOR_PICKUP


def test_cancel_request_on_item_at_desk_with_requests_at_home(
        client, item4_at_desk_martigny_patron_and_loan_at_desk,
        loc_public_martigny, librarian_martigny,
        patron2_martigny):
    """Test cancel requests on an at_desk item with requests at home."""
    item, patron, loan = item4_at_desk_martigny_patron_and_loan_at_desk
    # the following tests the circulation action CANCEL_REQUEST_2_1_2_2
    # an item at_desk with other pending loans.
    # pickup location of 1st pending loan = pickup location of current loan
    # cancel the current loan and item is: at_desk, automatic validation of
    # firt pending loan

    params = {
        'patron_pid': patron2_martigny.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid,
        'pickup_location_pid': loc_public_martigny.pid
    }
    item, requested_loan = item_record_to_a_specific_loan_state(
        item=item, loan_state=LoanState.PENDING,
        params=params, copy_item=False)
    assert requested_loan['state'] == LoanState.PENDING

    params = {
        'pid': loan.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    item.cancel_item_request(**params)
    item = Item.get_record_by_pid(item.pid)
    loan = Loan.get_record_by_pid(loan.pid)
    requested_loan = Loan.get_record_by_pid(requested_loan.pid)
    assert item.status == ItemStatus.AT_DESK
    assert loan['state'] == LoanState.CANCELLED
    assert requested_loan['state'] == LoanState.ITEM_AT_DESK


def test_cancel_pending_request_on_item_at_desk(
        client, item5_at_desk_martigny_patron_and_loan_at_desk,
        loc_public_martigny, librarian_martigny,
        patron2_martigny):
    """Test cancel requests on an at_desk item with requests at home."""
    item, patron, loan = item5_at_desk_martigny_patron_and_loan_at_desk
    # the following tests the circulation action CANCEL_REQUEST_2_2
    # an item at_desk with other pending loans. when a librarian wants to
    # cancel one of the pending loans. the item remains at_desk
    params = {
        'patron_pid': patron2_martigny.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid,
        'pickup_location_pid': loc_public_martigny.pid
    }
    item, requested_loan = item_record_to_a_specific_loan_state(
        item=item, loan_state=LoanState.PENDING,
        params=params, copy_item=False)
    assert requested_loan['state'] == LoanState.PENDING

    params = {
        'pid': requested_loan.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    item.cancel_item_request(**params)
    item = Item.get_record_by_pid(item.pid)
    loan = Loan.get_record_by_pid(loan.pid)
    requested_loan = Loan.get_record_by_pid(requested_loan.pid)
    assert item.status == ItemStatus.AT_DESK
    assert requested_loan['state'] == LoanState.CANCELLED
    assert loan['state'] == LoanState.ITEM_AT_DESK


def test_cancel_item_request_on_item_on_loan(
        client, item_on_loan_martigny_patron_and_loan_on_loan,
        loc_public_martigny, librarian_martigny,
        patron2_martigny):
    """Test cancel requests on an on_loan item."""
    item, patron, loan = item_on_loan_martigny_patron_and_loan_on_loan
    # the following tests the circulation action CANCEL_REQUEST_3_1
    # an item on_loan with no other pending loans. when a librarian wants to
    # cancel the on_loan loan. action is not permitted and item remain on_loan.
    params = {
        'pid': loan.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    with pytest.raises(NoCirculationAction):
        item.cancel_item_request(**params)
    item = Item.get_record_by_pid(item.pid)
    loan = Loan.get_record_by_pid(loan.pid)
    assert item.status == ItemStatus.ON_LOAN
    assert loan['state'] == LoanState.ITEM_ON_LOAN

    # the following tests the circulation action CANCEL_REQUEST_3_2
    # an item on_loan with other pending loans. when a librarian wants to
    # cancel the pending loan. action is permitted and item remains on_loan.
    params = {
        'patron_pid': patron2_martigny.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid,
        'pickup_location_pid': loc_public_martigny.pid
    }
    item, requested_loan = item_record_to_a_specific_loan_state(
        item=item, loan_state=LoanState.PENDING,
        params=params, copy_item=False)
    assert requested_loan['state'] == LoanState.PENDING

    params = {
        'pid': requested_loan.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    item.cancel_item_request(**params)
    item = Item.get_record_by_pid(item.pid)
    loan = Loan.get_record_by_pid(loan.pid)
    requested_loan = Loan.get_record_by_pid(requested_loan.pid)
    assert item.status == ItemStatus.ON_LOAN
    assert loan['state'] == LoanState.ITEM_ON_LOAN
    assert requested_loan['state'] == LoanState.CANCELLED


def test_cancel_item_request_on_item_in_transit_for_pickup(
        client, item_in_transit_martigny_patron_and_loan_for_pickup,
        loc_public_martigny, librarian_martigny,
        patron2_martigny):
    """Test cancel requests on an in_transit for pickup item."""
    item, patron, loan = item_in_transit_martigny_patron_and_loan_for_pickup
    # the following tests the circulation action CANCEL_REQUEST_4_1_1
    # an item in_transit for pickup with no other pending loans. when a
    # librarian wants to cancel the in_transit loan. action is permitted.
    # update loan, item is: in_transit (IN_TRANSIT_TO_HOUSE).
    params = {
        'pid': loan.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    item.cancel_item_request(**params)
    item = Item.get_record_by_pid(item.pid)
    loan = Loan.get_record_by_pid(loan.pid)
    assert item.status == ItemStatus.IN_TRANSIT
    assert loan['state'] == LoanState.ITEM_IN_TRANSIT_TO_HOUSE


def test_cancel_item_request_on_item_in_transit_for_pickup_with_requests(
        client, item2_in_transit_martigny_patron_and_loan_for_pickup,
        loc_public_martigny, librarian_martigny,
        patron2_martigny):
    """Test cancel requests on an in_transit for pickup item with requests."""
    item, patron, loan = item2_in_transit_martigny_patron_and_loan_for_pickup
    # the following tests the circulation action CANCEL_REQUEST_4_1_2
    # an item in_transit for pickup with other pending loans. when a
    # librarian wants to cancel the in_transit loan. action is permitted.
    # cancel loan, next pending loan is validated.

    params = {
        'patron_pid': patron2_martigny.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid,
        'pickup_location_pid': loc_public_martigny.pid
    }
    item, requested_loan = item_record_to_a_specific_loan_state(
        item=item, loan_state=LoanState.PENDING,
        params=params, copy_item=False)
    assert requested_loan['state'] == LoanState.PENDING

    params = {
        'pid': loan.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    item.cancel_item_request(**params)
    item = Item.get_record_by_pid(item.pid)
    loan = Loan.get_record_by_pid(loan.pid)
    requested_loan = Loan.get_record_by_pid(requested_loan.pid)
    assert item.status == ItemStatus.IN_TRANSIT
    assert loan['state'] == LoanState.CANCELLED
    assert requested_loan['state'] == LoanState.ITEM_IN_TRANSIT_FOR_PICKUP


def test_cancel_pending_loan_on_item_in_transit_for_pickup_with_requests(
        client, item3_in_transit_martigny_patron_and_loan_for_pickup,
        loc_public_martigny, librarian_martigny,
        patron2_martigny):
    """Test cancel pending loan on an in_transit for pickup item."""
    item, patron, loan = item3_in_transit_martigny_patron_and_loan_for_pickup
    # the following tests the circulation action CANCEL_REQUEST_4_2
    # an item in_transit for pickup with other pending loans. when a
    # librarian wants to cancel the pending loan. action is permitted.
    # item remains in_transit

    params = {
        'patron_pid': patron2_martigny.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid,
        'pickup_location_pid': loc_public_martigny.pid
    }
    item, requested_loan = item_record_to_a_specific_loan_state(
        item=item, loan_state=LoanState.PENDING,
        params=params, copy_item=False)
    assert requested_loan['state'] == LoanState.PENDING

    params = {
        'pid': requested_loan.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    item.cancel_item_request(**params)
    item = Item.get_record_by_pid(item.pid)
    loan = Loan.get_record_by_pid(loan.pid)
    requested_loan = Loan.get_record_by_pid(requested_loan.pid)
    assert item.status == ItemStatus.IN_TRANSIT
    assert loan['state'] == LoanState.ITEM_IN_TRANSIT_FOR_PICKUP
    assert requested_loan['state'] == LoanState.CANCELLED


def test_cancel_request_on_item_in_transit_to_house(
        client, item_in_transit_martigny_patron_and_loan_to_house,
        loc_public_martigny, librarian_martigny):
    """Test cancel request loan on an in_transit to_house item."""
    item, patron, loan = item_in_transit_martigny_patron_and_loan_to_house
    # the following tests the circulation action CANCEL_REQUEST_5_1_1
    # an item in_transit to house with no other loans. when a
    # librarian wants to cancel the in_transit loan. action is permitted.
    # the item will be checked in. at home, will go on_shelf
    params = {
        'pid': loan.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    item.cancel_item_request(**params)
    item = Item.get_record_by_pid(item.pid)
    loan = Loan.get_record_by_pid(loan.pid)
    assert item.status == ItemStatus.ON_SHELF
    assert loan['state'] == LoanState.CANCELLED


def test_cancel_request_on_item_in_transit_to_house_with_requests(
        client, item2_in_transit_martigny_patron_and_loan_to_house,
        loc_public_martigny, librarian_martigny,
        patron2_martigny):
    """Test cancel request on an in_transit to_house item with requests."""
    item, patron, loan = item2_in_transit_martigny_patron_and_loan_to_house
    # the following tests the circulation action CANCEL_REQUEST_5_1_2
    # an item in_transit to house with pending loans. when a
    # librarian wants to cancel the in_transit loan. action is permitted.
    # the loan will be cancelled. and first pending loan will be validated.
    params = {
        'patron_pid': patron2_martigny.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid,
        'pickup_location_pid': loc_public_martigny.pid
    }
    item, requested_loan = item_record_to_a_specific_loan_state(
        item=item, loan_state=LoanState.PENDING,
        params=params, copy_item=False)
    assert requested_loan['state'] == LoanState.PENDING

    params = {
        'pid': loan.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    item.cancel_item_request(**params)
    item = Item.get_record_by_pid(item.pid)
    loan = Loan.get_record_by_pid(loan.pid)
    requested_loan = Loan.get_record_by_pid(requested_loan.pid)
    assert item.status == ItemStatus.IN_TRANSIT
    assert loan['state'] == LoanState.CANCELLED
    assert requested_loan['state'] == LoanState.ITEM_IN_TRANSIT_FOR_PICKUP


def test_cancel_pending_on_item_in_transit_to_house(
        client, item3_in_transit_martigny_patron_and_loan_to_house,
        loc_public_martigny, librarian_martigny,
        patron2_martigny):
    """Test cancel pending loan on an in_transit to_house item."""
    item, patron, loan = item3_in_transit_martigny_patron_and_loan_to_house
    # the following tests the circulation action CANCEL_REQUEST_5_2
    # an item in_transit to house with pending loans. when a
    # librarian wants to cancel the pending loan. action is permitted.
    # the loan will be cancelled. and in_transit loan remains in transit.
    params = {
        'patron_pid': patron2_martigny.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid,
        'pickup_location_pid': loc_public_martigny.pid
    }
    item, requested_loan = item_record_to_a_specific_loan_state(
        item=item, loan_state=LoanState.PENDING,
        params=params, copy_item=False)
    assert requested_loan['state'] == LoanState.PENDING

    params = {
        'pid': requested_loan.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    item.cancel_item_request(**params)
    item = Item.get_record_by_pid(item.pid)
    loan = Loan.get_record_by_pid(loan.pid)
    requested_loan = Loan.get_record_by_pid(requested_loan.pid)
    assert item.status == ItemStatus.IN_TRANSIT
    assert loan['state'] == LoanState.ITEM_IN_TRANSIT_TO_HOUSE
    assert requested_loan['state'] == LoanState.CANCELLED
