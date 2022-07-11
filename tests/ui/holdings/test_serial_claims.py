# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2022 RERO
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


"""Serial claims tests."""

from __future__ import absolute_import, print_function

from copy import deepcopy
from datetime import datetime, timedelta

from rero_ils.modules.holdings.api import Holding
from rero_ils.modules.holdings.models import HoldingTypes
from rero_ils.modules.items.api import Item
from rero_ils.modules.items.models import ItemIssueStatus
from rero_ils.modules.items.tasks import process_late_issues
from rero_ils.modules.utils import get_ref_for_pid


def test_late_expected(
         holding_lib_martigny_w_patterns, holding_lib_sion_w_patterns,
         yesterday, tomorrow):
    """Test automatic change of late expected issues status to late."""
    martigny = holding_lib_martigny_w_patterns
    sion = holding_lib_sion_w_patterns

    def count_issues(holding):
        """Get holdings issues counts.

        output format: [late_issues_count]
        """
        late_issues = list(Item.get_issues_by_status(
            issue_status=ItemIssueStatus.LATE,
            holdings_pid=holding.pid
        ))
        return len(late_issues)

    # these two holdings has no late
    assert not count_issues(martigny)
    assert not count_issues(sion)

    # for these holdings records, the next expected date is already passed
    # system will receive the issue and change its status to late
    process_late_issues(dbcommit=True, reindex=True)
    assert count_issues(martigny) == 1
    assert count_issues(sion) == 1

    # create a second late issue for martigny and no more for sion
    sion['patterns']['next_expected_date'] = tomorrow.strftime('%Y-%m-%d')
    sion.update(sion, dbcommit=True, reindex=True)

    martigny['patterns']['next_expected_date'] = yesterday.strftime('%Y-%m-%d')
    martigny.update(martigny, dbcommit=True, reindex=True)

    process_late_issues(dbcommit=True, reindex=True)
    assert count_issues(martigny) == 2
    assert count_issues(sion) == 1

    # change the acq_status of Martigny holding.
    # as Martigny holding isn't yet considered as alive, no new issue should
    # be generated. The late issue count still the same (=2)
    martigny = Holding.get_record_by_pid(martigny.pid)
    martigny_data = deepcopy(martigny)
    date2 = datetime.now() - timedelta(days=1)
    martigny['patterns']['next_expected_date'] = date2.strftime('%Y-%m-%d')
    martigny['acquisition_status'] = 'not_currently_received'
    martigny.update(martigny, dbcommit=True, reindex=True)
    process_late_issues(dbcommit=True, reindex=True)
    assert count_issues(martigny) == 2  # no new late issue than before
    # reset Martigny holding
    martigny.update(martigny_data, dbcommit=True, reindex=True)


def test_items_after_holdings_update(
        holding_lib_martigny_w_patterns, item_type_on_site_martigny,
        loc_restricted_martigny):
    """Test location and item type after holdings of type serials changes."""
    martigny = holding_lib_martigny_w_patterns
    assert martigny.get('holdings_type') == HoldingTypes.SERIAL
    # ensure that all attached items of holdings record has the same location
    # and item type.
    item_pids = Item.get_items_pid_by_holding_pid(
        martigny.pid)
    for pid in item_pids:
        item = Item.get_record_by_pid(pid)
        assert item.location_pid == martigny.location_pid
        assert item.item_type_pid == martigny.circulation_category_pid

    assert martigny.location_pid != loc_restricted_martigny.pid
    assert martigny.circulation_category_pid != item_type_on_site_martigny.pid
    # change the holdings circulation_category and location.
    martigny['circulation_category'] = {'$ref': get_ref_for_pid(
        'item_types', item_type_on_site_martigny.pid)}
    martigny['location'] = {'$ref': get_ref_for_pid(
        'locations', loc_restricted_martigny.pid)}
    martigny = martigny.update(martigny, dbcommit=True, reindex=True)
    assert martigny.location_pid == loc_restricted_martigny.pid
    assert martigny.circulation_category_pid == item_type_on_site_martigny.pid
    # ensure that all attached items of holdings record has the same location
    # and item type after holdings changes.
    for pid in item_pids:
        item = Item.get_record_by_pid(pid)
        assert item.location_pid == martigny.location_pid
        assert item.item_type_pid == martigny.circulation_category_pid
