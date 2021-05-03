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


"""Serial claims tests."""

from __future__ import absolute_import, print_function

from copy import deepcopy
from datetime import datetime, timedelta, timezone

from rero_ils.modules.holdings.api import Holding
from rero_ils.modules.items.api import Item
from rero_ils.modules.items.models import ItemIssueStatus
from rero_ils.modules.items.tasks import process_late_claimed_issues


def test_late_expected_and_claimed_issues(
         holding_lib_martigny_w_patterns, holding_lib_sion_w_patterns,
         yesterday, tomorrow):
    """Test automatic change of late expected issues status to late
    and automatic change to claimed when issue is due"""
    martigny = holding_lib_martigny_w_patterns
    sion = holding_lib_sion_w_patterns

    def count_issues(holding):
        """Get holdings issues counts.

        output format: [late_issues_count, claimed_issues_count]
        """
        late_issues = list(Item.get_issues_by_status(
            issue_status=ItemIssueStatus.LATE,
            holdings_pid=holding.pid
        ))
        claimed_issues = list(Item.get_issues_by_status(
            issue_status=ItemIssueStatus.CLAIMED,
            holdings_pid=holding.pid
        ))
        return [len(late_issues), len(claimed_issues)]

    # these two holdings has no late or claimed issues
    assert count_issues(martigny) == [0, 0]
    assert count_issues(sion) == [0, 0]

    # for these holdings records, the next expected date is already passed
    # system will receive the issue and change its status to late
    process_late_claimed_issues(dbcommit=True, reindex=True)
    assert count_issues(martigny) == [1, 0]
    assert count_issues(sion) == [1, 0]

    # create a second late issue for martigny and no more for sion
    sion['patterns']['next_expected_date'] = tomorrow.strftime('%Y-%m-%d')
    sion.update(sion, dbcommit=True, reindex=True)

    martigny['patterns']['next_expected_date'] = yesterday.strftime('%Y-%m-%d')
    martigny.update(martigny, dbcommit=True, reindex=True)

    process_late_claimed_issues(dbcommit=True, reindex=True)
    assert count_issues(martigny) == [2, 0]
    assert count_issues(sion) == [1, 0]

    # change the acq_status of Martigny holding.
    # as Martigny holding isn't yet considerate as alive, no new issue should
    # be generated. The late issue count still the same (=2)
    martigny = Holding.get_record_by_pid(martigny.pid)
    martigny_data = deepcopy(martigny)
    date2 = datetime.now() - timedelta(days=1)
    martigny['patterns']['next_expected_date'] = date2.strftime('%Y-%m-%d')
    martigny['acquisition_status'] = 'not_currently_received'
    martigny.update(martigny, dbcommit=True, reindex=True)
    process_late_claimed_issues(dbcommit=True, reindex=True)
    assert count_issues(martigny) == [2, 0]  # no new late issue than before
    # reset Martigny holding
    martigny.update(martigny_data, dbcommit=True, reindex=True)

    # -- test the claiming process
    # create a first claim for an issue and the claim_counts will increment
    late_issue = list(Item.get_issues_by_status(
        issue_status=ItemIssueStatus.LATE, holdings_pid=martigny.pid))[0]
    late_issue['issue']['status_date'] = (
        datetime.now(timezone.utc)
        - timedelta(days=martigny.days_before_first_claim + 1)
    ).isoformat()
    late_issue.update(late_issue, dbcommit=True, reindex=True)

    assert late_issue.claims_count == 0
    process_late_claimed_issues(
        create_next_claim=False,
        dbcommit=True,
        reindex=True
    )
    assert count_issues(martigny) == [1, 1]
    assert count_issues(sion) == [1, 0]
    late_issue = Item.get_record_by_pid(late_issue.pid)
    assert late_issue.claims_count == 1

    # create the next claim for an issue and the claim_counts will increment
    late_issue['issue']['status_date'] = (
        datetime.now(timezone.utc)
        - timedelta(days=martigny.days_before_next_claim + 1)
    ).isoformat()
    late_issue.update(late_issue, dbcommit=True, reindex=True)
    process_late_claimed_issues(dbcommit=True, reindex=True)
    assert count_issues(martigny) == [1, 1]
    late_issue = Item.get_record_by_pid(late_issue.pid)
    assert late_issue.claims_count == 2

    # No more claims will be generated because the max claims reached
    process_late_claimed_issues(dbcommit=True, reindex=True)
    assert count_issues(martigny) == [1, 1]
    late_issue = Item.get_record_by_pid(late_issue.pid)
    assert late_issue.claims_count == 2
