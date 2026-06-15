# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test item circulation cancel request actions."""

from rero_ils.modules.items.models import ItemStatus
from rero_ils.modules.loans.api import Loan
from rero_ils.modules.loans.models import LoanAction, LoanState


def test_in_transit_second_request_at_home(
    app,
    item_lib_martigny,
    patron_martigny,
    patron2_martigny,
    librarian_martigny,
    loc_public_martigny,
    circulation_policies,
    loc_public_fully,
):
    """Test cases when in-transit loan is cancelled."""
    params = {
        "patron_pid": patron_martigny.pid,
        "transaction_location_pid": loc_public_martigny.pid,
        "transaction_user_pid": librarian_martigny.pid,
        "pickup_location_pid": loc_public_fully.pid,
    }
    assert item_lib_martigny.status == ItemStatus.ON_SHELF
    item, actions = item_lib_martigny.request(**params)
    first_loan = Loan.get_record_by_pid(actions[LoanAction.REQUEST].get("pid"))
    assert item_lib_martigny.status == ItemStatus.ON_SHELF
    assert first_loan["state"] == LoanState.PENDING
    item, actions = item.validate_request(**params, pid=first_loan.pid)
    first_loan = Loan.get_record_by_pid(actions[LoanAction.VALIDATE].get("pid"))
    assert item.status == ItemStatus.IN_TRANSIT
    assert first_loan["state"] == LoanState.ITEM_IN_TRANSIT_FOR_PICKUP

    params = {
        "patron_pid": patron2_martigny.pid,
        "transaction_location_pid": loc_public_martigny.pid,
        "transaction_user_pid": librarian_martigny.pid,
        "pickup_location_pid": loc_public_martigny.pid,
    }
    item, actions = item.request(**params)
    second_loan = Loan.get_record_by_pid(actions[LoanAction.REQUEST].get("pid"))
    assert item_lib_martigny.status == ItemStatus.IN_TRANSIT
    assert second_loan["state"] == LoanState.PENDING

    params = {
        "pid": first_loan.pid,
        "transaction_location_pid": loc_public_martigny.pid,
        "transaction_user_pid": librarian_martigny.pid,
    }
    item, actions = item.cancel_item_request(**params)
    first_loan = Loan.get_record_by_pid(first_loan.pid)
    second_loan = Loan.get_record_by_pid(second_loan.pid)
    assert item_lib_martigny.status == ItemStatus.IN_TRANSIT
    assert second_loan["state"] == LoanState.ITEM_IN_TRANSIT_FOR_PICKUP
    assert first_loan["state"] == LoanState.CANCELLED


def test_in_transit_second_request_externally(
    app,
    item2_lib_martigny,
    patron_martigny,
    patron2_martigny,
    librarian_martigny,
    loc_public_martigny,
    circulation_policies,
    loc_public_fully,
):
    """Test cases when in-transit loan is cancelled."""
    params = {
        "patron_pid": patron_martigny.pid,
        "transaction_location_pid": loc_public_martigny.pid,
        "transaction_user_pid": librarian_martigny.pid,
        "pickup_location_pid": loc_public_fully.pid,
    }
    assert item2_lib_martigny.status == ItemStatus.ON_SHELF
    item, actions = item2_lib_martigny.request(**params)
    first_loan = Loan.get_record_by_pid(actions[LoanAction.REQUEST].get("pid"))
    assert item2_lib_martigny.status == ItemStatus.ON_SHELF
    assert first_loan["state"] == LoanState.PENDING
    item, actions = item.validate_request(**params, pid=first_loan.pid)
    first_loan = Loan.get_record_by_pid(actions[LoanAction.VALIDATE].get("pid"))
    assert item.status == ItemStatus.IN_TRANSIT
    assert first_loan["state"] == LoanState.ITEM_IN_TRANSIT_FOR_PICKUP

    params = {
        "patron_pid": patron2_martigny.pid,
        "transaction_location_pid": loc_public_martigny.pid,
        "transaction_user_pid": librarian_martigny.pid,
        "pickup_location_pid": loc_public_fully.pid,
    }
    item, actions = item.request(**params)
    second_loan = Loan.get_record_by_pid(actions[LoanAction.REQUEST].get("pid"))
    assert item2_lib_martigny.status == ItemStatus.IN_TRANSIT
    assert second_loan["state"] == LoanState.PENDING

    params = {
        "pid": first_loan.pid,
        "transaction_location_pid": loc_public_martigny.pid,
        "transaction_user_pid": librarian_martigny.pid,
    }
    item, actions = item.cancel_item_request(**params)
    first_loan = Loan.get_record_by_pid(first_loan.pid)
    second_loan = Loan.get_record_by_pid(second_loan.pid)
    assert item2_lib_martigny.status == ItemStatus.IN_TRANSIT
    assert second_loan["state"] == LoanState.ITEM_IN_TRANSIT_FOR_PICKUP
    assert first_loan["state"] == LoanState.CANCELLED
