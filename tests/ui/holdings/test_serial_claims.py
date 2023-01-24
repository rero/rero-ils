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

from utils import flush_index

from rero_ils.modules.holdings.api import Holding
from rero_ils.modules.holdings.models import HoldingTypes
from rero_ils.modules.items.api import Item, ItemsSearch
from rero_ils.modules.items.models import ItemIssueStatus
from rero_ils.modules.items.tasks import process_late_issues
from rero_ils.modules.utils import get_ref_for_pid


def test_late_expected(
         holding_lib_martigny_w_patterns, holding_lib_sion_w_patterns,
         yesterday, tomorrow):
    """Test automatic change of late expected issues status to late."""
    martigny = holding_lib_martigny_w_patterns
    sion = holding_lib_sion_w_patterns

    def get_late_issues(holding):
        return Item.get_issues_by_status(
            ItemIssueStatus.LATE,
            holdings_pid=holding.pid
        )

    # these two holdings has no late
    assert not len(list(get_late_issues(martigny)))
    assert not len(list(get_late_issues(sion)))

    # for these holdings records, the need date is already passed
    # system will receive the issue and change its status to late
    process_late_issues(dbcommit=True, reindex=True)
    assert len(list(get_late_issues(martigny))) == 1
    assert len(list(get_late_issues(sion))) == 1

    # create a second late issue for Martigny and no more for Sion
    sion['patterns']['next_expected_date'] = tomorrow.strftime('%Y-%m-%d')
    sion.update(sion, dbcommit=True, reindex=True)
    martigny['patterns']['next_expected_date'] = yesterday.strftime('%Y-%m-%d')
    martigny.update(martigny, dbcommit=True, reindex=True)

    process_late_issues(dbcommit=True, reindex=True)
    assert len(list(get_late_issues(martigny))) == 2
    assert len(list(get_late_issues(sion))) == 1

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
    late_issues = list(get_late_issues(martigny))
    assert len(late_issues) == 2  # no new late issue than before

    # Get a late issues and update it's expected date : this will be set the
    # `sort_date` field
    issue = late_issues[0]
    assert issue.issue_status == ItemIssueStatus.LATE
    original_expected_date = issue.expected_date
    es_issue = ItemsSearch().get_record_by_pid(issue.pid)
    assert not issue.sort_date
    assert es_issue['issue']['sort_date'] == original_expected_date

    issue.expected_date = tomorrow.strftime('%Y-%m-%d')
    issue = issue.update(issue, dbcommit=True, reindex=True)
    assert issue.sort_date == original_expected_date
    assert issue.issue_status == ItemIssueStatus.EXPECTED

    # Now set the issue `expected_date` to an over date and run again the task.
    # The previous issue should be updated to `LATE` status
    issue.expected_date = yesterday.strftime('%Y-%m-%d')
    issue.update(issue, dbcommit=True, reindex=True)
    flush_index(ItemsSearch.Meta.index)
    process_late_issues(dbcommit=True, reindex=True)

    issue = Item.get_record_by_pid(issue.pid)
    assert issue.issue_status == ItemIssueStatus.LATE

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
