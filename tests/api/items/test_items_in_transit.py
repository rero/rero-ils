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

"""Tests items in-transit."""


from invenio_accounts.testutils import login_user_via_session

from rero_ils.modules.items.api import Item
from rero_ils.modules.items.models import ItemStatus
from rero_ils.modules.loans.models import LoanAction
from tests.utils import postdata


def test_items_in_transit_between_libraries(
    client,
    librarian_martigny,
    librarian_saxon,
    patron_martigny,
    loc_public_martigny,
    item_type_standard_martigny,
    loc_public_saxon,
    item_lib_martigny,
    json_header,
    circulation_policies,
):
    """Test item in-transit scenarios."""
    login_user_via_session(client, librarian_martigny.user)
    # checkout the item at location A
    res, data = postdata(
        client,
        "api_item.checkout",
        dict(
            item_pid=item_lib_martigny.pid,
            patron_pid=patron_martigny.pid,
            transaction_location_pid=loc_public_saxon.pid,
            transaction_user_pid=librarian_martigny.pid,
        ),
    )
    assert res.status_code == 200
    assert (
        Item.get_record_by_pid(item_lib_martigny.pid).get("status")
        == ItemStatus.ON_LOAN
    )
    item_data = data.get("metadata")
    actions = data.get("action_applied")
    assert item_data.get("status") == ItemStatus.ON_LOAN
    loan_pid = actions[LoanAction.CHECKOUT].get("pid")

    # checkin the item at location B
    res, data = postdata(
        client,
        "api_item.checkin",
        dict(
            item_pid=item_lib_martigny.pid,
            pid=loan_pid,
            transaction_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny.pid,
        ),
    )
    assert res.status_code == 200
    item_data = data.get("metadata")
    item = Item.get_record_by_pid(item_data.get("pid"))
    assert item.get("status") == ItemStatus.ON_SHELF
