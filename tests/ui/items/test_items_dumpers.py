# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2022-2024 RERO
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

"""Items Record dumper tests."""
from copy import deepcopy
from datetime import date

import pytest
from dateutil.relativedelta import relativedelta
from utils import item_record_to_a_specific_loan_state

from rero_ils.modules.collections.api import Collection
from rero_ils.modules.commons.exceptions import MissingDataException
from rero_ils.modules.holdings.api import Holding
from rero_ils.modules.items.dumpers import CirculationActionDumper, \
    ClaimIssueNotificationDumper, ItemCirculationDumper
from rero_ils.modules.items.models import TypeOfItem
from rero_ils.modules.loans.models import LoanState
from rero_ils.modules.utils import get_ref_for_pid


def test_item_action_circulation_dumper(
        item_lib_martigny, patron_martigny, loc_public_martigny,
        librarian_martigny, circulation_policies, loc_public_martigny_bourg,
        coll_martigny_1):
    """Test item circulation action dumper."""
    params = {
        'patron_pid': patron_martigny.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid,
        'pickup_location_pid': loc_public_martigny.pid,
    }
    item, _ = item_record_to_a_specific_loan_state(
        item=item_lib_martigny, loan_state=LoanState.PENDING,
        params=params, copy_item=False)

    data = item.dumps(CirculationActionDumper())
    # $ref resolution
    assert data['library']['pid']

    # document title
    assert data['document']['title']

    # location name
    assert data['location']['name']

    # organisation pid
    assert data['location']['organisation']['pid']

    # library and location name
    assert data['library_location_name']

    # actions
    assert data['actions']

    # pending loans
    assert len(data['pending_loans']) == 1

    # number of pending requests
    assert data['current_pending_requests'] == 1

    # not temporary location
    assert 'temporary_location' not in data

    # not collections
    assert 'collections' not in data

    # update end date on the collection
    collection = Collection.get_record_by_pid(coll_martigny_1["pid"])
    next_end_date = date.today() + relativedelta(months=2)
    collection["end_date"] = next_end_date.strftime("%Y-%m-%d")
    collection.update(collection, dbcommit=True, reindex=True)

    # add temporary location data
    item["temporary_location"] = {
        "pid": "loc15",
        "type": "loc"
    }

    data = item.dumps(CirculationActionDumper())

    # temporary location name
    assert data['temporary_location']['name'] == loc_public_martigny_bourg\
        .get('name')

    # Collection title
    assert data['collections'][0] == coll_martigny_1.get('title')


def test_item_circulation_dumper(item_lib_martigny):
    """Test item circulation dumper."""
    item = item_lib_martigny
    item['call_number'] = 'ITEM_MAIN_CN'
    item['second_call_number'] = 'ITEM_SECOND_CN'

    holdings = Holding.get_record_by_pid(item.holding_pid)
    original_holding_data = deepcopy(holdings)
    holdings['call_number'] = 'HOLDING_MAIN_CN'
    holdings['second_call_number'] = 'HOLDING_SECOND_CN'
    holdings.update(holdings, dbcommit=True, reindex=True)

    # CHECK_1 :: dumped call_numbers are equivalent to item call numbers
    dumped_data = item.dumps(dumper=ItemCirculationDumper())
    assert dumped_data['call_number'] == item['call_number']
    item.pop('call_number', None)
    dumped_data = item.dumps(dumper=ItemCirculationDumper())
    assert 'call_number' not in dumped_data
    assert dumped_data['second_call_number'] == item['second_call_number']

    # CHECK_2 :: remove all call_numbers from item, dumped date should
    #            integrate parent holdings call_numbers
    item.pop('second_call_number', None)
    dumped_data = item.dumps(dumper=ItemCirculationDumper())
    assert dumped_data['call_number'] == holdings['call_number']
    assert dumped_data['second_call_number'] == holdings['second_call_number']

    # RESET HOLDING RECORD
    holdings.update(original_holding_data, dbcommit=True, reindex=True)


def test_claim_issue_dumper(item_lib_martigny):
    """Test claim issue notification dumper."""
    with pytest.raises(TypeError):
        item_lib_martigny.dumps(dumper=ClaimIssueNotificationDumper())

    item_lib_martigny['type'] = TypeOfItem.ISSUE
    holding = item_lib_martigny.holding
    holding.pop('vendor', None)
    with pytest.raises(MissingDataException) as exc:
        item_lib_martigny.dumps(dumper=ClaimIssueNotificationDumper())
    assert 'item.holding.vendor' in str(exc)

    item_lib_martigny['holding']['$ref'] = get_ref_for_pid('hold', 'dummy')
    with pytest.raises(MissingDataException) as exc:
        item_lib_martigny.dumps(dumper=ClaimIssueNotificationDumper())
    assert 'item.holding' in str(exc)
