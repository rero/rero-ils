# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
# Copyright (C) 2019-2023 UCLouvain
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

"""Utilities functions about `Holdings` resource."""

from datetime import datetime, timedelta, timezone

from flask import current_app

from rero_ils.modules.errors import RegularReceiveNotAllowed
from rero_ils.modules.holdings.api import Holding, HoldingsSearch
from rero_ils.modules.items.models import ItemIssueStatus


def get_late_serial_holdings():
    """Return serial holdings with late issues.

    Holdings are considered late if :
      * holding type is `serial`
      * it's a `regular` serial holding (exclude irregular type)
      * it's considered as alive (acq_status='currently_received')
      * next expected date has passed (greater than current datetime).

    :return: A `Holding` resource generator
    """
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    yesterday = yesterday.strftime('%Y-%m-%d')
    query = HoldingsSearch() \
        .filter('term', holdings_type='serial') \
        .filter('term', acquisition_status='currently_received') \
        .filter('range', patterns__next_expected_date={'lte': yesterday}) \
        .exclude('term', patterns__frequency='rdafr:1016') \
        .source(False)
    for hit in query.scan():
        yield Holding.get_record(hit.meta.id)


def create_next_late_expected_issues(dbcommit=False, reindex=False):
    """Receive the next late expected issue for all holdings.

    :param reindex: reindex record by record.
    :param dbcommit: commit record to database.
    :return: the number of created issues.
    """
    counter = 0
    for holding in get_late_serial_holdings():
        try:
            issue = holding.create_regular_issue(
                status=ItemIssueStatus.LATE,
                dbcommit=dbcommit,
                reindex=reindex
            )
            issue.issue_status = ItemIssueStatus.LATE
            issue.update(issue, dbcommit=dbcommit, reindex=reindex)
            counter += 1
        except RegularReceiveNotAllowed as err:
            pid = holding.pid
            msg = f'Cannot receive next expected issue for Holding#{pid}'
            current_app.logger.error(f'{msg}::{str(err)}')
    return counter
