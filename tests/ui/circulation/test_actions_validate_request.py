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

"""Test item circulation validate request actions."""

import pytest
from invenio_circulation.errors import NoValidTransitionAvailableError

from rero_ils.modules.errors import NoCirculationAction
from rero_ils.modules.items.models import ItemStatus
from rero_ils.modules.loans.api import Loan
from rero_ils.modules.loans.models import LoanState
from tests.utils import item_record_to_a_specific_loan_state


def test_validate_on_item_on_shelf_no_requests(
    item_lib_martigny,
    patron_martigny,
    loc_public_martigny,
    librarian_martigny,
    circulation_policies,
):
    """Test validate a request on an on_shelf item with no requests."""
    # the following tests the circulation action VALIDATE_1_1
    # an on_shelf item with no pending requests.
    # no circulation action will be performed. no loan to validate.

    params = {
        "transaction_location_pid": loc_public_martigny.pid,
        "transaction_user_pid": librarian_martigny.pid,
    }
    with pytest.raises(NoCirculationAction):
        item, actions = item_lib_martigny.validate_request(**params)
    assert item_lib_martigny.status == ItemStatus.ON_SHELF


def test_validate_on_item_on_shelf_with_requests_at_home(
    item_on_shelf_martigny_patron_and_loan_pending,
    loc_public_martigny,
    librarian_martigny,
    circulation_policies,
):
    """Test validate a request on an on_shelf item with requests at home."""
    # the following tests the circulation action VALIDATE_1_2_1
    # an on_shelf item with pending requests.
    # the loan to validate loan goes to ITEM_AT_DESK if pickup library
    # equal to the transaction library.
    item, patron, loan = item_on_shelf_martigny_patron_and_loan_pending
    params = {
        "transaction_location_pid": loc_public_martigny.pid,
        "transaction_user_pid": librarian_martigny.pid,
        "pid": loan.pid,
    }
    item, actions = item.validate_request(**params)
    assert item.status == ItemStatus.AT_DESK
    loan = Loan.get_record_by_pid(loan.pid)
    assert loan["state"] == LoanState.ITEM_AT_DESK


def test_validate_on_item_on_shelf_with_requests_externally(
    item2_on_shelf_martigny_patron_and_loan_pending,
    loc_public_fully,
    loc_public_martigny,
    librarian_martigny,
    circulation_policies,
):
    """Test validate a request on an on_shelf item with requests externally."""
    # the following tests the circulation action VALIDATE_1_2_2
    # an on_shelf item with pending requests.
    # the loan to validate loan goes to ITEM_IN_TRANSIT_FOR_PICKUP if the
    # pickup library does not equal to the transaction library.
    item, patron, loan = item2_on_shelf_martigny_patron_and_loan_pending
    params = {
        "transaction_location_pid": loc_public_fully.pid,
        "transaction_user_pid": librarian_martigny.pid,
        "pid": loan.pid,
    }
    item, actions = item.validate_request(**params)
    assert item.status == ItemStatus.IN_TRANSIT
    loan = Loan.get_record_by_pid(loan.pid)
    assert loan["state"] == LoanState.ITEM_IN_TRANSIT_FOR_PICKUP


def test_validate_on_item_at_desk(
    item_at_desk_martigny_patron_and_loan_at_desk,
    loc_public_martigny,
    librarian_martigny,
    circulation_policies,
    patron2_martigny,
):
    """Test validate a request on an item at_desk."""
    # the following tests the circulation action VALIDATE_2
    # on at_desk item, the validation is not possible
    item, patron, loan = item_at_desk_martigny_patron_and_loan_at_desk
    params = {
        "transaction_location_pid": loc_public_martigny.pid,
        "transaction_user_pid": librarian_martigny.pid,
        "pid": loan.pid,
    }
    with pytest.raises(NoValidTransitionAvailableError):
        item, actions = item.validate_request(**params)
    assert item.status == ItemStatus.AT_DESK
    loan = Loan.get_record_by_pid(loan.pid)
    assert loan["state"] == LoanState.ITEM_AT_DESK
    # will not be able to validate any requestes for this item
    params = {
        "patron_pid": patron2_martigny.pid,
        "transaction_location_pid": loc_public_martigny.pid,
        "transaction_user_pid": librarian_martigny.pid,
        "pickup_location_pid": loc_public_martigny.pid,
    }
    item, requested_loan = item_record_to_a_specific_loan_state(
        item=item, loan_state=LoanState.PENDING, params=params, copy_item=False
    )
    params["pid"] = requested_loan.pid
    with pytest.raises(NoValidTransitionAvailableError):
        item, actions = item.validate_request(**params)
    requested_loan = Loan.get_record_by_pid(requested_loan.pid)
    assert requested_loan["state"] == LoanState.PENDING
    loan = Loan.get_record_by_pid(loan.pid)
    assert loan["state"] == LoanState.ITEM_AT_DESK


def test_validate_on_item_on_loan(
    item_on_loan_martigny_patron_and_loan_on_loan,
    loc_public_martigny,
    librarian_martigny,
    circulation_policies,
    patron2_martigny,
):
    """Test validate a request on an item on_loan."""
    # the following tests the circulation action VALIDATE_3
    # on on_loan item, the validation is not possible
    item, patron, loan = item_on_loan_martigny_patron_and_loan_on_loan
    params = {
        "transaction_location_pid": loc_public_martigny.pid,
        "transaction_user_pid": librarian_martigny.pid,
        "pid": loan.pid,
    }
    with pytest.raises(NoValidTransitionAvailableError):
        item, actions = item.validate_request(**params)
    assert item.status == ItemStatus.ON_LOAN
    loan = Loan.get_record_by_pid(loan.pid)
    assert loan["state"] == LoanState.ITEM_ON_LOAN

    # will not be able to validate any requestes for this item
    params = {
        "patron_pid": patron2_martigny.pid,
        "transaction_location_pid": loc_public_martigny.pid,
        "transaction_user_pid": librarian_martigny.pid,
        "pickup_location_pid": loc_public_martigny.pid,
    }
    item, requested_loan = item_record_to_a_specific_loan_state(
        item=item, loan_state=LoanState.PENDING, params=params, copy_item=False
    )
    params["pid"] = requested_loan.pid
    with pytest.raises(NoValidTransitionAvailableError):
        item, actions = item.validate_request(**params)
    requested_loan = Loan.get_record_by_pid(requested_loan.pid)
    assert requested_loan["state"] == LoanState.PENDING
    loan = Loan.get_record_by_pid(loan.pid)
    assert loan["state"] == LoanState.ITEM_ON_LOAN


def test_validate_on_item_in_transit_for_pickup(
    item_in_transit_martigny_patron_and_loan_for_pickup,
    loc_public_martigny,
    librarian_martigny,
    circulation_policies,
    patron2_martigny,
):
    """Test validate a request on an item in_transit for pickup."""
    # the following tests the circulation action VALIDATE_4
    # on on_loan item, the validation is not possible
    item, patron, loan = item_in_transit_martigny_patron_and_loan_for_pickup
    params = {
        "transaction_location_pid": loc_public_martigny.pid,
        "transaction_user_pid": librarian_martigny.pid,
        "pid": loan.pid,
    }
    with pytest.raises(NoValidTransitionAvailableError):
        item, actions = item.validate_request(**params)
    assert item.status == ItemStatus.IN_TRANSIT
    loan = Loan.get_record_by_pid(loan.pid)
    assert loan["state"] == LoanState.ITEM_IN_TRANSIT_FOR_PICKUP

    # will not be able to validate any requestes for this item
    params = {
        "patron_pid": patron2_martigny.pid,
        "transaction_location_pid": loc_public_martigny.pid,
        "transaction_user_pid": librarian_martigny.pid,
        "pickup_location_pid": loc_public_martigny.pid,
    }
    item, requested_loan = item_record_to_a_specific_loan_state(
        item=item, loan_state=LoanState.PENDING, params=params, copy_item=False
    )
    params["pid"] = requested_loan.pid
    with pytest.raises(NoValidTransitionAvailableError):
        item, actions = item.validate_request(**params)
    requested_loan = Loan.get_record_by_pid(requested_loan.pid)
    assert requested_loan["state"] == LoanState.PENDING
    loan = Loan.get_record_by_pid(loan.pid)
    assert loan["state"] == LoanState.ITEM_IN_TRANSIT_FOR_PICKUP


def test_validate_on_item_in_transit_to_house(
    item_in_transit_martigny_patron_and_loan_to_house,
    loc_public_martigny,
    librarian_martigny,
    circulation_policies,
    patron2_martigny,
):
    """Test validate a request on an item in_transit to house."""
    # the following tests the circulation action VALIDATE_5
    # on on_loan item, the validation is not possible
    item, patron, loan = item_in_transit_martigny_patron_and_loan_to_house
    params = {
        "transaction_location_pid": loc_public_martigny.pid,
        "transaction_user_pid": librarian_martigny.pid,
        "pid": loan.pid,
    }
    with pytest.raises(NoValidTransitionAvailableError):
        item, actions = item.validate_request(**params)
    assert item.status == ItemStatus.IN_TRANSIT
    loan = Loan.get_record_by_pid(loan.pid)
    assert loan["state"] == LoanState.ITEM_IN_TRANSIT_TO_HOUSE
    # will not be able to validate any requestes for this item
    params = {
        "patron_pid": patron2_martigny.pid,
        "transaction_location_pid": loc_public_martigny.pid,
        "transaction_user_pid": librarian_martigny.pid,
        "pickup_location_pid": loc_public_martigny.pid,
    }
    item, requested_loan = item_record_to_a_specific_loan_state(
        item=item, loan_state=LoanState.PENDING, params=params, copy_item=False
    )
    params["pid"] = requested_loan.pid
    with pytest.raises(NoValidTransitionAvailableError):
        item, actions = item.validate_request(**params)
    requested_loan = Loan.get_record_by_pid(requested_loan.pid)
    assert requested_loan["state"] == LoanState.PENDING
    loan = Loan.get_record_by_pid(loan.pid)
    assert loan["state"] == LoanState.ITEM_IN_TRANSIT_TO_HOUSE
