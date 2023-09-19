# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2022 RERO
# Copyright (C) 2022 UCLouvain
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

"""Test item circulation expired request actions."""
from datetime import datetime, timedelta, timezone

from freezegun import freeze_time
from utils import flush_index

from rero_ils.modules.items.api import Item
from rero_ils.modules.items.models import ItemStatus
from rero_ils.modules.loans.api import Loan, LoansSearch, get_expired_request
from rero_ils.modules.loans.logs.api import LoanOperationLog, \
    LoanOperationLogsSearch
from rero_ils.modules.loans.models import LoanState
from rero_ils.modules.loans.tasks import cancel_expired_request_task


@freeze_time("2022-03-01T14:33:22+02:00")
def test_expired_request_with_transit(
    item_lib_martigny, loc_public_sion, librarian_sion,
    loc_public_martigny, patron2_martigny, librarian_martigny,
    circulation_policies
):
    """Test request expiration for item in transit."""
    item = item_lib_martigny

    # STEP#0 :: INITIAL STATE
    #   * Create a request with a pick-up location different from the item
    #     location.
    #   * Validate this request/loan.
    #   * Receive this loan from the pick-up location
    item, actions = item.request(
        pickup_location_pid=loc_public_sion.pid,
        patron_pid=patron2_martigny.pid,
        transaction_location_pid=loc_public_martigny.pid,
        transaction_user_pid=librarian_martigny.pid
    )
    assert 'request' in actions
    loan = Loan.get_record_by_pid(actions['request']['pid'])
    assert item.location_pid != loan.pickup_location_pid

    item, _ = item.validate_request(
        transaction_location_pid=loc_public_martigny.pid,
        transaction_user_pid=librarian_martigny.pid,
        pid=loan.pid
    )
    loan = Loan.get_record_by_pid(loan.pid)
    assert item.status == ItemStatus.IN_TRANSIT
    assert loan.state == LoanState.ITEM_IN_TRANSIT_FOR_PICKUP

    item, _ = item.receive(
        transaction_location_pid=loc_public_sion.pid,
        transaction_user_pid=librarian_sion.pid,
        pid=loan.pid
    )
    loan = Loan.get_record_by_pid(loan.pid)
    assert item.status == ItemStatus.AT_DESK
    assert loan.state == LoanState.ITEM_AT_DESK
    assert 'request_expire_date' in loan

    # STEP#1 :: UPDATE THE LOAN TO SIMULATE REQUEST HAS EXPIRED
    #   Update the loan `request_expire_date` field to simulate than the
    #   requester patron never came take this item.
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    loan['request_expire_date'] = yesterday.isoformat()
    loan = loan.update(loan, dbcommit=True, reindex=True)
    flush_index(LoansSearch.Meta.index)
    assert loan.pid in [loan.pid for loan in get_expired_request()]

    # STEP#2 :: CANCEL THE EXPIRED REQUEST
    #   * Run the schedule task to cancel expired request
    #   * Check that the loan is now cancelled and it's status is
    #     IN_TRANSIT_TO_HOUSE
    #   * ensure than a "cancel" event was created into operation logs related
    #     to this loan
    task_result = cancel_expired_request_task()
    assert task_result == (1, 1)

    item = Item.get_record_by_pid(item.pid)
    loan = Loan.get_record_by_pid(loan.pid)
    assert item.status == ItemStatus.IN_TRANSIT
    assert loan.state == LoanState.ITEM_IN_TRANSIT_TO_HOUSE

    flush_index(LoanOperationLog.index_name)
    logs = LoanOperationLogsSearch().get_logs_by_record_pid(loan.pid)
    logs_trigger = [hit.loan.trigger for hit in logs]
    assert 'cancel' in logs_trigger

    # STEP#3 :: RECEIVE THE ITEM AT OWNING LIBRARY
    #   * Receive the item at the owning library.
    #   * Check than the item in now ON_SHELF
    #   * Check the loan state is now RETURNED
    item, _ = item.receive(
        transaction_location_pid=loc_public_martigny.pid,
        transaction_user_pid=librarian_martigny.pid,
        pid=loan.pid
    )
    loan = Loan.get_record_by_pid(loan.pid)
    assert item.status == ItemStatus.ON_SHELF
    assert loan.state == LoanState.ITEM_RETURNED
