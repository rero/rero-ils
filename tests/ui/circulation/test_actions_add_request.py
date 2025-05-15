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

from rero_ils.modules.loans.models import LoanState
from tests.utils import item_record_to_a_specific_loan_state


def test_add_request_on_item_on_shelf(
    item_on_shelf_martigny_patron_and_loan_pending,
    loc_public_martigny,
    librarian_martigny,
    patron2_martigny,
):
    """Test requests on an on_shelf item."""
    item, patron, loan = item_on_shelf_martigny_patron_and_loan_pending

    # the following tests the circulation action ADD_REQUEST_1_1
    # an on_shelf item with no pending requests can have new pending requests.
    assert loan["state"] == LoanState.PENDING

    # the following tests the circulation action ADD_REQUEST_1_2_1
    # for an item on_shelf with a pending loan, the patron that owns the
    # pending loan can not add a new pending loan on same item.
    params = {
        "patron_pid": patron.pid,
        "transaction_location_pid": loc_public_martigny.pid,
        "transaction_user_pid": librarian_martigny.pid,
        "pickup_location_pid": loc_public_martigny.pid,
    }
    with pytest.raises(RecordCannotBeRequestedError):
        item, loan = item_record_to_a_specific_loan_state(
            item=item, loan_state=LoanState.PENDING, params=params, copy_item=False
        )

    # the following tests the circulation action ADD_REQUEST_1_2_2
    # for an item on_shelf with a pending loan, a patron that does not own the
    # pending loan can add a new pending loan on same item.
    params["patron_pid"] = patron2_martigny.pid
    item, requested_loan = item_record_to_a_specific_loan_state(
        item=item, loan_state=LoanState.PENDING, params=params, copy_item=False
    )
    assert requested_loan["state"] == LoanState.PENDING


def test_add_request_on_item_at_desk(
    client,
    item_at_desk_martigny_patron_and_loan_at_desk,
    loc_public_martigny,
    librarian_martigny,
    patron2_martigny,
):
    """Test requests on an at_desk item."""
    item, patron, loan = item_at_desk_martigny_patron_and_loan_at_desk

    # the following tests the circulation action ADD_REQUEST_2_1
    # the patron owns the ITEM_AT_DESK loan may not create a new pending loan.
    params = {
        "patron_pid": patron.pid,
        "transaction_location_pid": loc_public_martigny.pid,
        "transaction_user_pid": librarian_martigny.pid,
        "pickup_location_pid": loc_public_martigny.pid,
    }
    with pytest.raises(RecordCannotBeRequestedError):
        item, loan = item_record_to_a_specific_loan_state(
            item=item, loan_state=LoanState.PENDING, params=params, copy_item=False
        )

    # the following tests the circulation action ADD_REQUEST_2_2
    # a patron who doesnt own the ITEM_AT_DESK loan can add a new pending loan.

    params["patron_pid"] = patron2_martigny.pid
    item, requested_loan = item_record_to_a_specific_loan_state(
        item=item, loan_state=LoanState.PENDING, params=params, copy_item=False
    )
    assert requested_loan["state"] == LoanState.PENDING
    assert loan["state"] == LoanState.ITEM_AT_DESK


def test_add_request_on_item_on_loan(
    item_on_loan_martigny_patron_and_loan_on_loan,
    loc_public_martigny,
    librarian_martigny,
    patron2_martigny,
    patron4_martigny,
):
    """Test requests on an on_loan item."""
    item, patron, loan = item_on_loan_martigny_patron_and_loan_on_loan

    # the following tests the circulation action ADD_REQUEST_3_1
    # the patron owns the ITEM_ON_LOAN loan may not create a new pending loan.
    params = {
        "patron_pid": patron.pid,
        "transaction_location_pid": loc_public_martigny.pid,
        "transaction_user_pid": librarian_martigny.pid,
        "pickup_location_pid": loc_public_martigny.pid,
    }
    with pytest.raises(RecordCannotBeRequestedError):
        item, loan = item_record_to_a_specific_loan_state(
            item=item, loan_state=LoanState.PENDING, params=params, copy_item=False
        )

    # the following tests the circulation action ADD_REQUEST_3_2_1
    # any patron who does not own the ITEM_ON_LOAN loan can add a new pending
    # loan.
    params["patron_pid"] = patron2_martigny.pid
    item, requested_loan = item_record_to_a_specific_loan_state(
        item=item, loan_state=LoanState.PENDING, params=params, copy_item=False
    )
    assert requested_loan["state"] == LoanState.PENDING
    assert loan["state"] == LoanState.ITEM_ON_LOAN

    # the following tests the circulation action ADD_REQUEST_3_2_2_1
    # when an item on_loan has pending requests, the patron who owns the
    # pending loan may not add a new pending loan
    params["patron_pid"] = patron2_martigny.pid
    with pytest.raises(RecordCannotBeRequestedError):
        item, requested_loan = item_record_to_a_specific_loan_state(
            item=item, loan_state=LoanState.PENDING, params=params, copy_item=False
        )
    # the following tests the circulation action ADD_REQUEST_3_2_2_2
    # when an item on_loan has pending requests, any patron who does not own
    # the pending loan may add a new pending loan
    params["patron_pid"] = patron4_martigny.pid
    item, second_requested_loan = item_record_to_a_specific_loan_state(
        item=item, loan_state=LoanState.PENDING, params=params, copy_item=False
    )
    assert loan["state"] == LoanState.ITEM_ON_LOAN
    assert requested_loan["state"] == LoanState.PENDING
    assert second_requested_loan["state"] == LoanState.PENDING


def test_add_request_on_item_in_transit_for_pickup(
    item_in_transit_martigny_patron_and_loan_for_pickup,
    loc_public_martigny,
    librarian_martigny,
    patron2_martigny,
    loc_public_fully,
):
    """Test requests on an in_transit item for pickup."""
    item, patron, loan = item_in_transit_martigny_patron_and_loan_for_pickup

    # the following tests the circulation action ADD_REQUEST_4_1
    # the owner of the IN_TRANSIT_FOR_PICKUP loan can not add a pending loan
    params = {
        "patron_pid": patron.pid,
        "transaction_location_pid": loc_public_martigny.pid,
        "transaction_user_pid": librarian_martigny.pid,
        "pickup_location_pid": loc_public_fully.pid,
    }
    with pytest.raises(RecordCannotBeRequestedError):
        item, loan = item_record_to_a_specific_loan_state(
            item=item, loan_state=LoanState.PENDING, params=params, copy_item=False
        )

    # the following tests the circulation action ADD_REQUEST_4_2
    # a patron who does not own the IN_TRANSIT_FOR_PICKUP loan can add
    # a new pending loan.
    params["patron_pid"] = patron2_martigny.pid
    item, requested_loan = item_record_to_a_specific_loan_state(
        item=item, loan_state=LoanState.PENDING, params=params, copy_item=False
    )
    assert requested_loan["state"] == LoanState.PENDING
    assert loan["state"] == LoanState.ITEM_IN_TRANSIT_FOR_PICKUP


def test_add_request_on_item_in_transit_to_house(
    item_in_transit_martigny_patron_and_loan_to_house,
    loc_public_martigny,
    librarian_martigny,
    patron2_martigny,
    loc_public_fully,
    patron4_martigny,
):
    """Test requests on an in_transit item to house."""
    item, patron, loan = item_in_transit_martigny_patron_and_loan_to_house

    # the following tests the circulation action ADD_REQUEST_5_1
    # any patron can add a new pending loan on an item with a loan equal to
    # ITEM_IN_TRANSIT_TO_HOUSE
    params = {
        "patron_pid": patron2_martigny.pid,
        "transaction_location_pid": loc_public_martigny.pid,
        "transaction_user_pid": librarian_martigny.pid,
        "pickup_location_pid": loc_public_martigny.pid,
        "checkin_transaction_location_pid": loc_public_fully.pid,
    }
    item, requested_loan = item_record_to_a_specific_loan_state(
        item=item, loan_state=LoanState.PENDING, params=params, copy_item=False
    )
    assert loan["state"] == LoanState.ITEM_IN_TRANSIT_TO_HOUSE
    assert requested_loan["state"] == LoanState.PENDING

    # the following tests the circulation action ADD_REQUEST_5_2_1
    # when a pending loan exist on an item with loan ITEM_IN_TRANSIT_TO_HOUSE
    # the patron who owns the pending loan can not add a new pending loan
    with pytest.raises(RecordCannotBeRequestedError):
        item, requested_loan = item_record_to_a_specific_loan_state(
            item=item, loan_state=LoanState.PENDING, params=params, copy_item=False
        )

    # the following tests the circulation action ADD_REQUEST_5_2_2
    # when a pending loan exist on an item with loan ITEM_IN_TRANSIT_TO_HOUSE,
    # any patron who does now own the pending loan can add a new pending loan.
    params["patron_pid"] = patron4_martigny.pid
    item, second_requested_loan = item_record_to_a_specific_loan_state(
        item=item, loan_state=LoanState.PENDING, params=params, copy_item=False
    )
    assert loan["state"] == LoanState.ITEM_IN_TRANSIT_TO_HOUSE
    assert second_requested_loan["state"] == LoanState.PENDING
    assert requested_loan["state"] == LoanState.PENDING
