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

"""Item record extensions."""
from datetime import datetime

import ciso8601
from invenio_records.extensions import RecordExtension

from rero_ils.modules.items.models import ItemIssueStatus


class IssueSortDateExtension(RecordExtension):
    """Extension to control the `sort_date` field for an `issue` Item.

    If the item is an issue, the `sort_date` field is used as default sort
    filter. This `sort_date` is an optional field ; so in ElasticSearch, if
    no `sort_date` value is present, we use the `expected_date` as sort key.
    But, when an issue comes to 'LATE' status, a manager could update this
    `expected_date` for a new one without filling the `sort_date` (to keep the
    best possible order). In this case, this extension will fill the
    `sort_date` field with the original `expected_date` value.
    """

    def pre_commit(self, record, **kwargs):
        """Called before a record is committed.

        :param record: the record metadata.
        :param kwargs: any additional named arguments.
        """
        # If record isn't an issue or `sort_date` is already set. No more
        # operations must be done.
        if not record.is_issue or record.sort_date:
            return

        # Compare `expected_date` value from current record and db_record. If
        # value changes then use the `db_record.expected_date` as `sort_date`
        db_record = record.db_record()
        if db_record.expected_date != record.expected_date:
            record.sort_date = db_record.expected_date or record.expected_date


class IssueStatusExtension(RecordExtension):
    """Extension to manage the issue status depending on expected date.

    Manager could manually update the `expected_date` of an issue. If the
    expected date is in the future, then the issue status must always be set
    to `expected` regardless current status.
    """

    @staticmethod
    def _control_status(record):
        """Control and update issue status if necessary.

        :param record: the record metadata.
        """
        # It could happen that manager would change the `expected_date`
        # when the issue status is late/claimed (because editor give a new
        # date) BUT this manager could forget to update the issue status to
        # 'expected' in this case, this extension will automatically change
        # the issue status.
        if (
            record.issue_status == ItemIssueStatus.LATE and
            record.received_date
        ):
            record['issue'].pop('received_date', None)
        invalid_statuses = [ItemIssueStatus.LATE]
        if record.is_issue and record.issue_status in invalid_statuses:
            expected_date = ciso8601.parse_datetime(record.expected_date)
            if expected_date >= datetime.now():
                record.issue_status = ItemIssueStatus.EXPECTED

    def pre_commit(self, record, **kwargs):
        """Called before a record is committed.

        :param record: the record metadata.
        :param kwargs: any additional named arguments.
        """
        IssueStatusExtension._control_status(record)

    def pre_create(self, record, **kwargs):
        """Called before a record is created.

        :param record: the record metadata.
        :param kwargs: any additional named arguments.
        """
        IssueStatusExtension._control_status(record)
        if record.model:
            record.model.data = record
