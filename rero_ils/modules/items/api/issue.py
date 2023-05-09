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

"""API for manipulating the item issue."""

from .record import ItemRecord
from ..models import TypeOfItem
from ...notifications.api import NotificationsSearch


class ItemIssue(ItemRecord):
    """Item issue class."""

    @property
    def is_issue(self):
        """Is this item is an issue or not."""
        return self.get('type') == TypeOfItem.ISSUE

    @property
    def expected_date(self):
        """Shortcut for issue expected date."""
        return self.get('issue', {}).get('expected_date')

    @expected_date.setter
    def expected_date(self, value):
        """Setter for the issue expected date."""
        self.setdefault('issue', {})['expected_date'] = value

    @property
    def received_date(self):
        """Shortcut for issue received date."""
        return self.get('issue', {}).get('received_date')

    @property
    def sort_date(self):
        """Shortcut for issue sort date."""
        return self.get('issue', {}).get('sort_date')

    @sort_date.setter
    def sort_date(self, value):
        """Setter for the issue sort date."""
        self.setdefault('issue', {})['sort_date'] = value

    @property
    def issue_status(self):
        """Shortcut for issue status."""
        return self.get('issue', {}).get('status')

    @issue_status.setter
    def issue_status(self, value):
        """Setter for issue status."""
        self.setdefault('issue', {})['status'] = value

    @property
    def issue_is_regular(self):
        """Shortcut for issue is regular."""
        return self.get('issue', {}).get('regular', True)

    @property
    def issue_status_date(self):
        """Shortcut for issue status date."""
        return self.get('issue', {}).get('status_date')

    @property
    def vendor_pid(self):
        """Shortcut for vendor pid if exists."""
        if (holding := self.holding) and (vendor := holding.vendor):
            return vendor.pid

    @property
    def claims_count(self):
        """Get the number of claims notification sent about this issue."""
        return len(list(NotificationsSearch().get_claims(self.pid)))

    @property
    def issue_inherited_first_call_number(self):
        """Get issue inherited first call number.

        When the issue first call number is missing,
        it returns the parent holdings first call number if exists.
        """
        from rero_ils.modules.holdings.api import Holding
        if self.is_issue and not self.get('call_number'):
            holding = Holding.get_record_by_pid(self.holding_pid)
            return holding.get('call_number')

    @classmethod
    def get_issues_pids_by_status(cls, issue_status, holdings_pid=None):
        """Return issues pids by status optionally filtered by holdings_pid.

        :param holdings_pid: the holdings pid. If none, return all late issues.
        :param issue_status: the issue status.
        :return a generator of issues pid.
        """
        from .api import ItemsSearch
        query = ItemsSearch() \
            .filter('term', issue__status=issue_status) \
            .filter('term', type='issue')
        if holdings_pid:
            query = query.filter('term', holding__pid=holdings_pid)
        query = query\
            .params(preserve_order=True) \
            .sort({'_created': {'order': 'asc'}}) \
            .source(['pid'])

        return [hit.pid for hit in query.scan()]

    @classmethod
    def get_issues_by_status(cls, status, holdings_pid=None):
        """Return all issues by status optionally filtered for a holdings pid.

        :param status: the status of the issue.
        :param holdings_pid: the holdings pid. If none, return all late issues.
        :return a generator of Item.
        """
        from .api import Item
        for pid in cls.get_issues_pids_by_status(status, holdings_pid):
            yield Item.get_record_by_pid(pid)
