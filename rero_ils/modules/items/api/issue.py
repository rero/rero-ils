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

"""API for manipulating the item issue."""

from datetime import datetime, timezone

import ciso8601
from flask import current_app

from .record import ItemRecord
from ..models import ItemIssueStatus, TypeOfItem


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
    def claims_count(self):
        """Shortcut for the issue claims_count."""
        return self.get('issue', {}).get('claims_count', 0)

    @claims_count.setter
    def claims_count(self, value):
        """Setter for issue claims counter."""
        self.setdefault('issue', {})['claims_count'] = value

    @property
    def vendor_pid(self):
        """Shortcut for vendor pid if exists."""
        from ...holdings.api import Holding
        if self.holding_pid:
            holding = Holding.get_record_by_pid(self.holding_pid)
            if vendor := holding.vendor:
                return vendor.pid

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

    @classmethod
    def _process_issue_claim(cls, issue, claims_days, dbcommit=False,
                             reindex=False):
        """Process issue for a new claim.

        :param issue: the issue item record.
        :param reindex: reindex the records.
        :param dbcommit: commit record to database.
        :return a count of modified issues.
        """
        update_counts = 0
        if cls._get_issue_status_age(issue) >= claims_days:
            cls._update_issue_status_claims_count(
                issue, dbcommit=dbcommit, reindex=reindex)
            update_counts += 1
        return update_counts

    @classmethod
    def _get_issue_status_age(cls, issue):
        """Return the age of an issue.

        It compares the issue status date with the current timestamp

        :param issue: the issue item record.
        :return the issue status age in days.
        """
        issue_status_date = ciso8601.parse_datetime(
            issue.issue_status_date)
        return (datetime.now(timezone.utc) - issue_status_date).days

    @classmethod
    def _update_issue_status_claims_count(
            cls, issue, dbcommit=False, reindex=False):
        """Update issue status and claims count.

        It compares the issue status date with the current timestamp

        :param issue: the issue item record.
        :param reindex: reindex the records.
        :param dbcommit: commit record to database.
        """
        issue['issue']['status'] = ItemIssueStatus.CLAIMED
        issue.claims_count += 1
        issue.update(issue, dbcommit=dbcommit, reindex=reindex)

    @classmethod
    def create_first_and_next_claims(cls, claim_type=None, dbcommit=False,
                                     reindex=False):
        """Claim the late and claimed issues for all holdings.

        :param claim_type: if "first", it creates the first claim for late
            issues. if "next", it creates the next claim for claimed issues.
        :param reindex: is the issues should be reindex.
        :param dbcommit: is the issues should be committed into database.
        :return: a count of modified issues.
        """
        from rero_ils.modules.holdings.api import Holding

        assert claim_type in ['first', 'next'], 'Invalid claim type'
        issue_status = ItemIssueStatus.CLAIMED  # default for 'next' claim type
        if claim_type == 'first':
            issue_status = ItemIssueStatus.LATE

        issues = cls.get_issues_by_status(issue_status) if issue_status else []
        modified_issues = 0
        holdings_cache = {}

        for issue in issues:
            try:
                # Load the holding if not already loaded. If related holding
                # doesn't exist, raise an error.
                holding_pid = issue.holding_pid
                if holding_pid not in holdings_cache:
                    holding = Holding.get_record_by_pid(issue.holding_pid)
                    if not holding:
                        raise KeyError(f'Unable to load holding#{holding_pid}')
                    holdings_cache[holding.pid] = holding

                # Determine if the maximum of claims is already done. If yes,
                # skip this issue.
                holding = holdings_cache.get(holding_pid)
                if issue.claims_count >= holding.max_number_of_claims:
                    raise ValueError('Maximum claim reached')

                # Try to get the related vendor email. If not found, raise an
                # error and skip the claim creation process.
                if not (vendor := holding.vendor) or not vendor.order_email:
                    raise ValueError(f'holding#{holding_pid} : Unable to find '
                                     f'an related vendor email')

                # run the claim process for this issue
                if issue.claims_count == 0:
                    claims_days = holding.days_before_first_claim
                else:
                    claims_days = holding.days_before_next_claim
                modified_issues += cls._process_issue_claim(
                    issue=issue,
                    claims_days=claims_days,
                    dbcommit=dbcommit,
                    reindex=reindex
                )
            except Exception as err:
                current_app.logger.error(
                    f'Can not create {claim_type} '
                    f'claim for issue: {issue.pid} error: {str(err)}'
                )
        return modified_issues
