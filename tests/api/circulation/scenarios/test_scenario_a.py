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

"""Tests circulation scenario A."""


from invenio_accounts.testutils import login_user_via_session
from utils import get_json, postdata

from rero_ils.modules.items.models import ItemStatus
from rero_ils.modules.loans.api import Loan
from rero_ils.modules.operation_logs.api import OperationLogsSearch


def test_circ_scenario_a(
    client,
    librarian_martigny,
    lib_martigny,
    patron_martigny,
    loc_public_martigny,
    item_lib_martigny,
    circulation_policies,
):
    """Test the first circulation scenario."""
    # https://github.com/rero/rero-ils/blob/dev/doc/circulation/scenarios.md
    # A request is made on on-shelf item, that has no requests, to be picked
    # up at the owning library. Validated by the librarian. Picked up at same
    # owning library. and returned on-time at the owning library
    login_user_via_session(client, librarian_martigny.user)
    circ_params = {
        "item_pid": item_lib_martigny.pid,
        "patron_pid": patron_martigny.pid,
        "pickup_location_pid": loc_public_martigny.pid,
        "transaction_library_pid": lib_martigny.pid,
        "transaction_user_pid": librarian_martigny.pid,
    }
    # ADD_REQUEST_1.1
    res, data = postdata(client, "api_item.librarian_request", dict(circ_params))
    assert res.status_code == 200
    request_loan_pid = get_json(res)["action_applied"]["request"]["pid"]
    # VALIDATE_1.2
    circ_params["pid"] = request_loan_pid
    res, data = postdata(client, "api_item.validate_request", dict(circ_params))
    assert res.status_code == 200
    loan = Loan(get_json(res)["action_applied"]["validate"])
    assert loan.checkout_date is None
    # CHECKOUT_2.1
    res, data = postdata(client, "api_item.checkout", dict(circ_params))
    assert res.status_code == 200
    loan = Loan(get_json(res)["action_applied"]["checkout"])
    OperationLogsSearch.flush_and_refresh()
    assert loan.checkout_date
    # CHECKIN_3.1.1
    res, data = postdata(client, "api_item.checkin", dict(circ_params))
    assert res.status_code == 200
    assert item_lib_martigny.status == ItemStatus.ON_SHELF
