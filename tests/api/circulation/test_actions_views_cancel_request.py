# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests REST cancel item request API methods in the item api_views."""

from invenio_accounts.testutils import login_user_via_session

from rero_ils.modules.items.api import Item
from rero_ils.modules.items.models import ItemStatus
from rero_ils.modules.loans.api import Loan
from rero_ils.modules.loans.models import LoanState
from tests.utils import postdata


def test_cancel_an_item_request(
    client,
    librarian_martigny,
    lib_martigny,
    item_at_desk_martigny_patron_and_loan_at_desk,
    item_on_shelf_martigny_patron_and_loan_pending,
    loc_public_martigny,
    circulation_policies,
):
    """Test the frontend cancel an item request action."""
    # test passes when all required parameters are given
    login_user_via_session(client, librarian_martigny.user)
    item, patron, loan = item_on_shelf_martigny_patron_and_loan_pending

    # test fails when there is a missing required parameter
    res, data = postdata(client, "api_item.cancel_item_request", {"pid": loan.pid})
    assert res.status_code == 400

    # test fails when there is a missing required parameter
    res, data = postdata(
        client,
        "api_item.cancel_item_request",
        {"pid": loan.pid, "transaction_location_pid": loc_public_martigny.pid},
    )
    assert res.status_code == 400

    # test fails when there is a missing required parameter
    # when item record not found in database, api returns 404
    res, data = postdata(
        client,
        "api_item.cancel_item_request",
        {
            "transaction_location_pid": loc_public_martigny.pid,
            "transaction_user_pid": librarian_martigny.pid,
        },
    )
    assert res.status_code == 404

    # test passes when the transaction location pid is given
    res, data = postdata(
        client,
        "api_item.cancel_item_request",
        {
            "pid": loan.pid,
            "transaction_location_pid": loc_public_martigny.pid,
            "transaction_user_pid": librarian_martigny.pid,
        },
    )
    assert res.status_code == 200

    # test passes when the transaction library pid is given
    login_user_via_session(client, librarian_martigny.user)
    item, patron, loan = item_at_desk_martigny_patron_and_loan_at_desk
    res, data = postdata(
        client,
        "api_item.cancel_item_request",
        {
            "pid": loan.pid,
            "transaction_library_pid": lib_martigny.pid,
            "transaction_user_pid": librarian_martigny.pid,
        },
    )
    assert res.status_code == 200


def test_cancel_an_item_request_at_desk_in_another_library(
    client,
    librarian_martigny,
    lib_martigny,
    item_martigny_at_desk_fully_patron_and_loan_at_desk,
    circulation_policies,
):
    """Test the frontend cancel of a request at desk in an external library."""
    # A martigny item is at desk in the fully library, its request is
    # cancelled by a librarian of the owning library: the item must go back
    # home instead of going on shelf.
    item, patron, loan = item_martigny_at_desk_fully_patron_and_loan_at_desk
    login_user_via_session(client, librarian_martigny.user)
    res, _ = postdata(
        client,
        "api_item.cancel_item_request",
        {
            "pid": loan.pid,
            "transaction_library_pid": lib_martigny.pid,
            "transaction_user_pid": librarian_martigny.pid,
        },
    )
    assert res.status_code == 200
    assert Item.get_record_by_pid(item.pid).status == ItemStatus.IN_TRANSIT
    assert Loan.get_record_by_pid(loan.pid)["state"] == LoanState.ITEM_IN_TRANSIT_TO_HOUSE
