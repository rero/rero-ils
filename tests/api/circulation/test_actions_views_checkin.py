# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests REST return an item API methods in the item api_views."""

from datetime import UTC, date, datetime, timedelta

from flask import url_for
from flask_babel import gettext as _
from invenio_accounts.testutils import login_user_via_session

from rero_ils.modules.items.api import Item
from rero_ils.modules.items.models import ItemStatus
from rero_ils.modules.loans.api import Loan
from rero_ils.modules.loans.models import LoanState
from rero_ils.modules.loans.utils import get_circ_policy, sum_for_fees
from rero_ils.modules.operation_logs.api import OperationLogsSearch
from rero_ils.modules.patron_transactions.utils import get_last_transaction_by_loan_pid
from tests.utils import get_json, postdata


def test_checkin_an_item(
    client,
    librarian_martigny,
    lib_martigny,
    item_on_loan_martigny_patron_and_loan_on_loan,
    loc_public_martigny,
    item2_on_loan_martigny_patron_and_loan_on_loan,
    circulation_policies,
):
    """Test the frontend return a checked-out item action."""
    # test passes when all required parameters are given
    login_user_via_session(client, librarian_martigny.user)
    item, patron, loan = item_on_loan_martigny_patron_and_loan_on_loan

    # test fails when there is a missing required parameter
    res, data = postdata(client, "api_item.checkin", {"item_pid": item.pid})
    assert res.status_code == 400

    # test fails when there is a missing required parameter
    res, data = postdata(
        client,
        "api_item.checkin",
        {"item_pid": item.pid, "transaction_location_pid": loc_public_martigny.pid},
    )
    assert res.status_code == 400

    # test fails when there is a missing required parameter
    # when item record not found in database, api returns 404
    res, data = postdata(
        client,
        "api_item.checkin",
        {
            "transaction_location_pid": loc_public_martigny.pid,
            "transaction_user_pid": librarian_martigny.pid,
        },
    )
    assert res.status_code == 404

    # test passes when the transaction location pid is given
    res, data = postdata(
        client,
        "api_item.checkin",
        {
            "item_pid": item.pid,
            "transaction_location_pid": loc_public_martigny.pid,
            "transaction_user_pid": librarian_martigny.pid,
        },
    )
    assert res.status_code == 200
    item = Item.get_record_by_pid(item.pid)
    assert item.status == ItemStatus.ON_SHELF

    # test passes when the transaction library pid is given
    item, patron, loan = item2_on_loan_martigny_patron_and_loan_on_loan
    res, data = postdata(
        client,
        "api_item.checkin",
        {
            "item_pid": item.pid,
            "transaction_library_pid": lib_martigny.pid,
            "transaction_user_pid": librarian_martigny.pid,
        },
    )
    assert res.status_code == 200
    item = Item.get_record_by_pid(item.pid)
    assert item.status == ItemStatus.ON_SHELF


def test_auto_checkin_else(
    client,
    librarian_martigny,
    patron_martigny,
    loc_public_martigny,
    item_lib_martigny,
    json_header,
    lib_martigny,
    loc_public_saxon,
):
    """Test item checkin no action."""
    login_user_via_session(client, librarian_martigny.user)
    res, data = postdata(
        client,
        "api_item.checkin",
        {
            "item_pid": item_lib_martigny.pid,
            "transaction_library_pid": lib_martigny.pid,
            "transaction_user_pid": librarian_martigny.pid,
        },
    )
    assert res.status_code == 400
    assert get_json(res)["status"] == 400
    assert get_json(res)["message"] == _("No circulation action performed: on shelf")
    query = OperationLogsSearch().filter("term", record__type="scan_item").filter("exists", field="scan")
    assert query.count() == 1
    log_data = query.execute()[0].to_dict()
    assert log_data["scan"]["note"] == "No circulation action performed: on shelf"


def test_checkin_overdue_item(
    client,
    librarian_martigny,
    patron2_martigny,
    loc_public_martigny,
    item_on_loan_martigny_patron_and_loan_on_loan,
):
    """Test a checkin for an overdue item with incremental fees."""
    item, patron, loan = item_on_loan_martigny_patron_and_loan_on_loan

    # Update the circulation policy corresponding to the loan
    # Update the loan due date
    cipo = get_circ_policy(loan)
    cipo["overdue_fees"] = {
        "intervals": [
            {"from": 1, "to": 5, "fee_amount": 0.50},
            {"from": 6, "to": 10, "fee_amount": 1},
            {"from": 11, "fee_amount": 2},
        ]
    }
    cipo.update(data=cipo, dbcommit=True, reindex=True)
    end = date.today() - timedelta(days=30)
    end = datetime(end.year, end.month, end.day, tzinfo=UTC)
    end = end - timedelta(microseconds=1)
    loan["end_date"] = end.isoformat()
    loan = loan.update(loan, dbcommit=True, reindex=True)

    fees = loan.get_overdue_fees
    total_fees = sum_for_fees(fees)
    assert len(fees) > 0
    assert total_fees > 0

    # Check overdues preview API and check result
    loan_url = url_for("api_loan.preview_loan_overdue", loan_pid=loan.pid)
    patron_url = url_for("api_patrons.patron_overdue_preview_api", patron_pid=patron.pid)

    res = client.get(loan_url)
    assert res.status_code == 401
    res = client.get(patron_url)
    assert res.status_code == 401

    login_user_via_session(client, patron.user)
    res = client.get(loan_url)
    assert res.status_code == 200
    res = client.get(patron_url)
    assert res.status_code == 200

    assert patron.pid != patron2_martigny.pid
    login_user_via_session(client, patron2_martigny.user)
    res = client.get(loan_url)
    assert res.status_code == 403
    res = client.get(patron_url)
    assert res.status_code == 403

    login_user_via_session(client, librarian_martigny.user)
    res = client.get(loan_url)
    data = get_json(res)
    assert res.status_code == 200
    assert len(data["steps"]) > 0
    assert data["total"] > 0

    res = client.get(patron_url)
    data = get_json(res)
    assert res.status_code == 200
    assert len(data) == 1
    assert data[0]["loan"]["pid"] == loan.pid
    assert len(data[0]["fees"]["steps"]) > 0
    assert data[0]["fees"]["total"] > 0

    # Do the checkin on the item
    res, data = postdata(
        client,
        "api_item.checkin",
        {
            "item_pid": item.pid,
            "transaction_location_pid": loc_public_martigny.pid,
            "transaction_user_pid": librarian_martigny.pid,
        },
    )
    assert res.status_code == 200
    item = Item.get_record_by_pid(item.pid)
    assert item.status == ItemStatus.ON_SHELF

    # check if overdue transaction are created
    trans = get_last_transaction_by_loan_pid(loan.pid)
    assert trans.total_amount == total_fees
    events = list(trans.events)
    assert len(events) == 1
    assert len(events[0].get("steps", [])) == len(fees)

    # reset the cipo
    del cipo["overdue_fees"]
    cipo.update(data=cipo, dbcommit=True, reindex=True)


def test_checkin_scan_log_transaction_location(
    client,
    librarian_fully,
    lib_fully,
    loc_public_fully,
    loc_public_martigny,
    item_at_desk_martigny_patron_and_loan_at_desk,
):
    """Test the scan log keeps the location where the item was really scanned."""
    # An item at desk for a Martigny pickup is wrongly sent to Fully. The scan
    # log must reference the Fully location and not the last transaction
    # location recorded on the loan (Martigny).
    item, patron, loan = item_at_desk_martigny_patron_and_loan_at_desk
    assert loan["transaction_location_pid"] == loc_public_martigny.pid

    login_user_via_session(client, librarian_fully.user)
    res, _ = postdata(
        client,
        "api_item.checkin",
        {
            "item_pid": item.pid,
            "transaction_location_pid": loc_public_fully.pid,
            "transaction_user_pid": librarian_fully.pid,
        },
    )
    assert res.status_code == 400

    query = OperationLogsSearch().filter("term", scan__item__pid=item.pid)
    assert query.count() == 1
    log_data = query.execute()[0].to_dict()
    assert log_data["library"]["value"] == lib_fully.pid
    assert log_data["scan"]["transaction_location"]["pid"] == loc_public_fully.pid
    assert log_data["scan"]["pickup_location"]["pid"] == loc_public_martigny.pid

    # restore the fixture state: the checkin sent the item in transit
    loan = Loan.get_record_by_pid(loan.pid)
    loan["state"] = LoanState.ITEM_AT_DESK
    loan.update(loan, dbcommit=True, reindex=True)
    item = Item.get_record_by_pid(item.pid)
    item["status"] = ItemStatus.AT_DESK
    item.update(item, dbcommit=True, reindex=True)


def test_checkin_scan_log_transaction_location_in_transit(
    client,
    librarian_saxon,
    lib_saxon,
    loc_public_saxon,
    loc_public_fully,
    loc_public_martigny,
    item_in_transit_martigny_patron_and_loan_for_pickup,
):
    """Test the scan log of an in transit item scanned in a third library."""
    # An item in transit to Fully is scanned in Saxon. The scan log must
    # reference a Saxon location, resolved from the transaction library, and
    # not the transaction location recorded on the loan (Martigny).
    item, patron, loan = item_in_transit_martigny_patron_and_loan_for_pickup
    assert loan["transaction_location_pid"] == loc_public_martigny.pid

    login_user_via_session(client, librarian_saxon.user)
    res, _ = postdata(
        client,
        "api_item.checkin",
        {
            "item_pid": item.pid,
            "transaction_library_pid": lib_saxon.pid,
            "transaction_user_pid": librarian_saxon.pid,
        },
    )
    assert res.status_code == 400

    query = OperationLogsSearch().filter("term", scan__item__pid=item.pid)
    assert query.count() == 1
    log_data = query.execute()[0].to_dict()
    assert log_data["scan"]["transaction_location"]["pid"] == loc_public_saxon.pid
    assert log_data["scan"]["pickup_location"]["pid"] == loc_public_fully.pid
