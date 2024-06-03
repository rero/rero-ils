# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
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

"""Tests REST checkout API methods in library with no circulation."""

from datetime import datetime

from invenio_accounts.testutils import login_user_via_session
from utils import postdata

from rero_ils.modules.items.api import Item
from rero_ils.modules.items.models import ItemStatus
from rero_ils.modules.loans.api import Loan, LoanState
from rero_ils.modules.locations.api import Location


def test_checking_out_external_items_at_non_circ_library(
    client,
    librarian_martigny,
    lib_martigny,
    lib_martigny_bourg,
    patron_martigny,
    loc_public_martigny,
    loc_public_martigny_bourg,
    item_lib_martigny_bourg,
    circulation_policies,
    item_lib_martigny,
    librarian_martigny_bourg,
):
    """Test checkout of external items at non-circ library."""
    login_user_via_session(client, librarian_martigny_bourg.user)
    # A non-circulation library (has no pickup configured) and library hours is
    # well configured
    opening_hours = [
        {
            "day": "monday",
            "is_open": True,
            "times": [{"start_time": "07:00", "end_time": "19:00"}],
        }
    ]
    lib_martigny_bourg["opening_hours"] = opening_hours
    lib_martigny_bourg.update(lib_martigny_bourg, dbcommit=True, reindex=True)
    # a librarian from the non-circulating library can checkout items from
    # another library into his library
    params = dict(
        item_pid=item_lib_martigny.pid,
        patron_pid=patron_martigny.pid,
        transaction_user_pid=librarian_martigny_bourg.pid,
        transaction_library_pid=lib_martigny_bourg.pid,
    )
    res, data = postdata(client, "api_item.checkout", params)
    assert res.status_code == 200
    # the checkin is possible at the non-circulating library and the item goes
    # directly to in-transit
    res, data = postdata(
        client,
        "api_item.checkin",
        dict(
            item_pid=item_lib_martigny.pid,
            transaction_library_pid=lib_martigny_bourg.pid,
            transaction_user_pid=librarian_martigny_bourg.pid,
        ),
    )
    assert res.status_code == 200
    item = Item.get_record_by_pid(item_lib_martigny.pid)
    assert item.status == ItemStatus.IN_TRANSIT


def test_requesting_item_from_non_circulating_library(
    client,
    librarian_martigny,
    lib_martigny,
    lib_martigny_bourg,
    loc_restricted_martigny_bourg,
    patron_martigny,
    loc_public_martigny,
    loc_public_martigny_bourg,
    item_lib_martigny_bourg,
    circulation_policies,
    librarian_martigny_bourg,
):
    """Test requests on items of a non-circulating library."""
    login_user_via_session(client, librarian_martigny_bourg.user)
    # Test a checkout of an item at a library with open-hours and no pickup
    # locations defined is possible.
    opening_hours = [
        {
            "day": "monday",
            "is_open": True,
            "times": [{"start_time": "07:00", "end_time": "19:00"}],
        }
    ]
    lib_martigny_bourg["opening_hours"] = opening_hours
    lib_martigny_bourg.update(lib_martigny_bourg, dbcommit=True, reindex=True)
    params = dict(
        item_pid=item_lib_martigny_bourg.pid,
        patron_pid=patron_martigny.pid,
        transaction_user_pid=librarian_martigny_bourg.pid,
        transaction_library_pid=lib_martigny_bourg.pid,
    )
    res, data = postdata(client, "api_item.checkout", params)
    assert res.status_code == 200
    loan_pid = data.get("action_applied").get("checkout").get("pid")
    loan = Loan.get_record_by_pid(loan_pid)
    transaction_loc = Location.get_record_by_pid(loan.transaction_location_pid)
    assert transaction_loc.library_pid == lib_martigny_bourg.pid
    pickup_lib_pid = Location.get_record_by_pid(loan.pickup_location_pid).library_pid
    assert pickup_lib_pid == lib_martigny_bourg.pid
    assert loan.get("state") == LoanState.ITEM_ON_LOAN

    res, data = postdata(
        client,
        "api_item.checkin",
        dict(
            item_pid=item_lib_martigny_bourg.pid,
            transaction_library_pid=lib_martigny_bourg.pid,
            transaction_user_pid=librarian_martigny_bourg.pid,
        ),
    )
    assert res.status_code == 200
    item = Item.get_record_by_pid(item_lib_martigny_bourg.pid)
    assert item.status == ItemStatus.ON_SHELF

    # TEST: a librarian from an external library can request and item from a
    # non-circulating library to be picked-up at his own library.
    lib_martigny_bourg.pop("opening_hours", None)
    lib_martigny_bourg.update(lib_martigny_bourg, dbcommit=True, reindex=True)

    login_user_via_session(client, librarian_martigny.user)
    res, data = postdata(
        client,
        "api_item.librarian_request",
        dict(
            item_pid=item_lib_martigny_bourg.pid,
            patron_pid=patron_martigny.pid,
            pickup_location_pid=loc_public_martigny.pid,
            transaction_library_pid=lib_martigny_bourg.pid,
            transaction_user_pid=librarian_martigny.pid,
        ),
    )
    assert res.status_code == 200
    loan = Loan(data.get("metadata").get("pending_loans")[0])
    transaction_loc = Location.get_record_by_pid(loan.transaction_location_pid)
    assert transaction_loc.library_pid == lib_martigny_bourg.pid
    pickup_lib_pid = Location.get_record_by_pid(loan.pickup_location_pid).library_pid
    assert pickup_lib_pid == lib_martigny.pid

    # non-circulating library send items to requesting library
    login_user_via_session(client, librarian_martigny_bourg.user)
    res, data = postdata(
        client,
        "api_item.validate_request",
        dict(
            pid=loan.get("pid"),
            transaction_library_pid=lib_martigny_bourg.pid,
            transaction_user_pid=librarian_martigny_bourg.pid,
        ),
    )
    assert res.status_code == 200
    loan = Loan(data.get("metadata").get("pending_loans")[0])
    transaction_loc = Location.get_record_by_pid(loan.transaction_location_pid)
    assert transaction_loc.library_pid == lib_martigny_bourg.pid
    pickup_lib_pid = Location.get_record_by_pid(loan.pickup_location_pid).library_pid
    assert pickup_lib_pid == lib_martigny.pid

    assert loan.get("state") == LoanState.ITEM_IN_TRANSIT_FOR_PICKUP

    # requesting library receives an item from non-circulating library.
    login_user_via_session(client, librarian_martigny.user)
    res, data = postdata(
        client,
        "api_item.receive",
        dict(
            pid=loan.get("pid"),
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny.pid,
        ),
    )
    assert res.status_code == 200
    loan = Loan(data.get("metadata").get("pending_loans")[0])

    transaction_loc = Location.get_record_by_pid(loan.transaction_location_pid)
    assert transaction_loc.library_pid == lib_martigny.pid
    pickup_lib_pid = Location.get_record_by_pid(loan.pickup_location_pid).library_pid
    assert pickup_lib_pid == lib_martigny.pid

    assert loan.get("state") == LoanState.ITEM_AT_DESK

    # checkout item to requested patron
    login_user_via_session(client, librarian_martigny.user)
    date_format = "%Y/%m/%dT%H:%M:%S.000Z"
    today = datetime.utcnow()
    eod = today.replace(
        hour=23, minute=59, second=0, microsecond=0, tzinfo=lib_martigny.get_timezone()
    )
    params = dict(
        item_pid=item_lib_martigny_bourg.pid,
        patron_pid=patron_martigny.pid,
        transaction_user_pid=librarian_martigny.pid,
        transaction_library_pid=lib_martigny.pid,
        end_date=eod.strftime(date_format),
    )
    res, data = postdata(client, "api_item.checkout", params)
    assert res.status_code == 200
    loan_pid = data.get("action_applied").get("checkout").get("pid")
    loan = Loan.get_record_by_pid(loan_pid)

    transaction_loc = Location.get_record_by_pid(loan.transaction_location_pid)
    assert transaction_loc.library_pid == lib_martigny.pid
    pickup_lib_pid = Location.get_record_by_pid(loan.pickup_location_pid).library_pid
    assert pickup_lib_pid == lib_martigny.pid

    assert loan.get("state") == LoanState.ITEM_ON_LOAN
