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

"""Tests REST checkout API methods in the item api_views."""
from datetime import datetime, timedelta

import ciso8601
from invenio_accounts.testutils import login_user_via_session

from rero_ils.modules.items.models import ItemStatus
from tests.utils import postdata


def test_checkout_missing_parameters(
    client,
    librarian_martigny,
    lib_martigny,
    loc_public_martigny,
    patron_martigny,
    item_lib_martigny,
    circulation_policies,
):
    """Test checkout with missing parameters.

    Are needed:
        - item_pid_value
        - patron_pid
        - transaction_location_pid or transaction_library_pid
        - transaction_user_pid
    """
    login_user_via_session(client, librarian_martigny.user)
    item = item_lib_martigny
    assert item.status == ItemStatus.ON_SHELF

    # test fails when missing required parameter
    res, _ = postdata(client, "api_item.checkout", dict(item_pid=item.pid))
    assert res.status_code == 400
    res, _ = postdata(
        client,
        "api_item.checkout",
        dict(item_pid=item.pid, patron_pid=patron_martigny.pid),
    )
    assert res.status_code == 400
    res, _ = postdata(
        client,
        "api_item.checkout",
        dict(
            item_pid=item.pid,
            patron_pid=patron_martigny.pid,
            transaction_user_pid=librarian_martigny.pid,
        ),
    )
    assert res.status_code == 400


def test_checkout(
    client,
    librarian_martigny,
    lib_martigny,
    loc_public_martigny,
    patron_martigny,
    item_lib_martigny,
    circulation_policies,
    item_on_shelf_martigny_patron_and_loan_pending,
):
    """Test a successful frontend checkout action."""
    login_user_via_session(client, librarian_martigny.user)
    item = item_lib_martigny
    assert item.status == ItemStatus.ON_SHELF

    params = dict(
        item_pid=item.pid,
        patron_pid=patron_martigny.pid,
        transaction_user_pid=librarian_martigny.pid,
        transaction_location_pid=loc_public_martigny.pid,
    )

    # test is done WITHOUT loan PID
    res, _ = postdata(client, "api_item.checkout", params)
    assert res.status_code == 200

    # test WITH loan PID & WITH SPECIFIED END-DATE
    item, patron_pid, loan = item_on_shelf_martigny_patron_and_loan_pending
    assert item.status == ItemStatus.ON_SHELF
    params["item_pid"] = item.pid
    params["pid"] = loan.pid
    res, _ = postdata(client, "api_item.checkout", params)
    assert res.status_code == 200

    # TEST CHECKOUT WITH SPECIFIED END-DATE
    #   0) do a check-in for the item
    #   1) Ensure than Saturday is a closed day for the loc_public_martigny
    #   2) Try a checkout
    #   3) Ensure than checkout response return a transaction end_date == next
    #      business open day
    res, _ = postdata(
        client,
        "api_item.checkin",
        dict(
            item_pid=item.pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny.pid,
        ),
    )
    assert res.status_code == 200

    now = datetime.now()
    delta = timedelta((12 - now.weekday()) % 7)
    next_saturday = now + delta
    assert not lib_martigny.is_open(next_saturday, True)

    params = dict(
        item_pid=item.pid,
        patron_pid=patron_martigny.pid,
        transaction_user_pid=librarian_martigny.pid,
        transaction_location_pid=loc_public_martigny.pid,
        end_date=next_saturday.isoformat(),
    )
    res, data = postdata(client, "api_item.checkout", params)
    assert res.status_code == 200
    transaction_end_date = data["action_applied"]["checkout"]["end_date"]
    transaction_end_date = ciso8601.parse_datetime(transaction_end_date)
    next_open_date = lib_martigny.next_open(next_saturday)
    assert next_open_date.date() == transaction_end_date.date()
