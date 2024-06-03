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

"""In house circulation policy tests."""

from copy import deepcopy

import ciso8601
from freezegun import freeze_time
from utils import login_user_via_session, postdata

from rero_ils.modules.items.api import Item
from rero_ils.modules.items.models import ItemStatus
from rero_ils.modules.libraries.api import Library
from rero_ils.modules.loans.api import Loan
from rero_ils.modules.loans.models import LoanAction, LoanState


def test_less_than_one_day_checkout(
    client,
    circ_policy_less_than_one_day_martigny,
    patron_martigny,
    patron2_martigny,
    item_lib_martigny,
    loc_public_martigny,
    librarian_martigny,
    item_on_shelf_martigny_patron_and_loan_pending,
):
    """Test checkout on an ON_SHELF item with 'less than one day' cipo."""
    # Create a new item in ON_SHELF (without Loan)
    data = deepcopy(item_lib_martigny)
    data.pop("barcode")
    data.setdefault("status", ItemStatus.ON_SHELF)
    created_item = Item.create(data=data, dbcommit=True, reindex=True, delete_pid=True)

    # Check item is ON_SHELF and NO PENDING loan exist!
    assert created_item.number_of_requests() == 0
    assert created_item.status == ItemStatus.ON_SHELF
    assert not created_item.is_requested_by_patron(
        patron2_martigny.get("patron", {}).get("barcode")[0]
    )

    # Ensure than the transaction date used will be an open_day.
    owner_lib = Library.get_record_by_pid(created_item.library_pid)
    transaction_date = owner_lib.next_open(ensure=True)

    with freeze_time(transaction_date):
        # the following tests the circulation action CHECKOUT_1_1
        # an ON_SHELF item
        # WITHOUT pending loan
        # CAN be CHECKOUT for less than one day
        login_user_via_session(client, librarian_martigny.user)
        res, data = postdata(
            client,
            "api_item.checkout",
            dict(
                item_pid=created_item.pid,
                patron_pid=patron2_martigny.pid,
                transaction_location_pid=loc_public_martigny.pid,
                transaction_user_pid=librarian_martigny.pid,
                pickup_location_pid=loc_public_martigny.pid,
            ),
        )
        assert res.status_code == 200
        actions = data["action_applied"]
        onloan_item = Item.get_record_by_pid(data["metadata"]["pid"])
        loan = Loan.get_record_by_pid(actions[LoanAction.CHECKOUT].get("pid"))
        # Check loan is ITEM_ON_LOAN and item is ON_LOAN
        assert onloan_item.number_of_requests() == 0
        assert onloan_item.status == ItemStatus.ON_LOAN
        assert loan["state"] == LoanState.ITEM_ON_LOAN

        loan_end_date = ciso8601.parse_datetime(loan.get("end_date"))
        loan_end_date_formatted = loan_end_date.strftime("%Y-%m-%d")
        transaction_date_formatted = transaction_date.strftime("%Y-%m-%d")
        assert loan_end_date_formatted == transaction_date_formatted
