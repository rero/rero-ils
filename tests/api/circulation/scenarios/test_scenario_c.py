# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests circulation scenario C."""

from invenio_accounts.testutils import login_user_via_session

from rero_ils.modules.items.models import ItemStatus
from rero_ils.modules.loans.api import Loan
from tests.utils import get_json, postdata


def test_circ_scenario_c(
    client,
    librarian_martigny,
    lib_martigny,
    lib_saxon,
    patron_martigny,
    loc_public_martigny,
    item_lib_martigny,
    circulation_policies,
    loc_public_saxon,
    librarian_saxon,
    patron2_martigny,
    lib_fully,
    loc_public_fully,
    librarian_fully,
):
    """Test the third circulation scenario."""
    # https://github.com/rero/rero-ils/blob/dev/doc/circulation/scenarios.md
    # A request is made on item of library A, on-shelf without previous
    # requests, to be picked up at library B. Validated by the librarian A
    # and goes in transit. Received by the librarian B and goes at desk.
    # Picked up at library B. Requested by another patron_2 to be picked up
    # at library C. Returned on-time at the library B, goes in transit to
    # library C. Received at library C and goes at desk. Picked up at library C
    #  by patron_2. Renewed by patron_2. Returned on-time at the library C
    # after the end of first renewal. goes in transit to library A. Received at
    #  library A and goes on shelf.

    login_user_via_session(client, librarian_martigny.user)
    circ_params = {
        "item_pid": item_lib_martigny.pid,
        "patron_pid": patron_martigny.pid,
        "pickup_location_pid": loc_public_saxon.pid,
        "transaction_library_pid": lib_martigny.pid,
        "transaction_user_pid": librarian_martigny.pid,
    }
    res, data = postdata(client, "api_item.librarian_request", dict(circ_params))
    assert res.status_code == 200
    request_loan_pid = get_json(res)["action_applied"]["request"]["pid"]

    circ_params["pid"] = request_loan_pid
    res, data = postdata(client, "api_item.validate_request", dict(circ_params))
    assert res.status_code == 200

    login_user_via_session(client, librarian_saxon.user)

    circ_params = {
        "item_pid": item_lib_martigny.pid,
        "patron_pid": patron_martigny.pid,
        "pickup_location_pid": loc_public_saxon.pid,
        "transaction_library_pid": lib_saxon.pid,
        "transaction_user_pid": librarian_saxon.pid,
    }
    res, data = postdata(client, "api_item.checkin", dict(circ_params))
    assert res.status_code == 200

    res, data = postdata(client, "api_item.checkout", dict(circ_params))
    assert res.status_code == 200

    circ_params = {
        "item_pid": item_lib_martigny.pid,
        "patron_pid": patron2_martigny.pid,
        "pickup_location_pid": loc_public_fully.pid,
        "transaction_library_pid": lib_fully.pid,
        "transaction_user_pid": librarian_fully.pid,
    }
    res, data = postdata(client, "api_item.librarian_request", dict(circ_params))
    assert res.status_code == 200
    fully_loan_pid = get_json(res)["action_applied"]["request"]["pid"]

    circ_params = {
        "item_pid": item_lib_martigny.pid,
        "patron_pid": patron_martigny.pid,
        "pickup_location_pid": loc_public_saxon.pid,
        "transaction_library_pid": lib_saxon.pid,
        "transaction_user_pid": librarian_saxon.pid,
    }
    res, data = postdata(client, "api_item.checkin", dict(circ_params))
    assert res.status_code == 200
    assert item_lib_martigny.status == ItemStatus.ON_SHELF

    login_user_via_session(client, librarian_fully.user)
    circ_params = {
        "item_pid": item_lib_martigny.pid,
        "patron_pid": patron2_martigny.pid,
        "pickup_location_pid": loc_public_fully.pid,
        "transaction_library_pid": lib_fully.pid,
        "transaction_user_pid": librarian_fully.pid,
    }
    res, data = postdata(client, "api_item.checkout", dict(circ_params))
    assert res.status_code == 200

    # Update loan end_date to allow direct renewal
    loan = Loan.get_record_by_pid(data["action_applied"]["checkout"]["pid"])
    loan["end_date"] = loan["start_date"]
    loan.update(loan, dbcommit=True, reindex=True)

    res, data = postdata(client, "api_item.extend_loan", dict(circ_params))
    assert res.status_code == 200

    res, data = postdata(client, "api_item.checkin", dict(circ_params))
    assert res.status_code == 200

    login_user_via_session(client, librarian_martigny.user)
    circ_params = {
        "item_pid": item_lib_martigny.pid,
        "patron_pid": patron2_martigny.pid,
        "pickup_location_pid": loc_public_martigny.pid,
        "transaction_library_pid": lib_martigny.pid,
        "transaction_user_pid": librarian_martigny.pid,
    }
    res, data = postdata(client, "api_item.checkin", dict(circ_params))
    assert res.status_code == 200
    assert item_lib_martigny.status == ItemStatus.ON_SHELF
