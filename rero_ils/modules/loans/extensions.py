# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
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

"""RERO ILS common record extensions."""


from datetime import timedelta, timezone

import ciso8601
from invenio_records.extensions import RecordExtension


class SetDueSoonDate(RecordExtension):
    """Set the due soon date when the loan is updated."""

    def pre_commit(self, record):
        """Add the due soon date.

        :param record: the record metadata.
        """
        from .api import LoanState
        from .utils import get_circ_policy
        if record.state == LoanState.ITEM_ON_LOAN and record.get('end_date'):
            circ_policy = get_circ_policy(record)
            due_date = ciso8601.parse_datetime(record.end_date).replace(
                tzinfo=timezone.utc)
            days_before = circ_policy.due_soon_interval_days
            if days_before:
                due_soon = due_date - timedelta(days=days_before)
                due_soon = due_soon.replace(
                    hour=0, minute=0, second=0, microsecond=0)
                record['due_soon_date'] = due_soon.isoformat()
