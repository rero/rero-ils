# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
# Copyright (C) 2021 UCLouvain
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


from datetime import datetime, timedelta, timezone

import ciso8601
from flask import current_app
from invenio_records.extensions import RecordExtension

from rero_ils.modules.libraries.exceptions import LibraryNeverOpen
from rero_ils.modules.loans.models import LoanState


class CirculationDatesExtension(RecordExtension):
    """Add some dates to manage circulation operation."""

    @staticmethod
    def _add_request_expiration_date(record):
        """Add the request expiration date to record is needed.

        When a request is validated, we need to set the `request_expire_date`
        field with the expiration date of this request. When this date is
        reached and item is still AT_DESK, this request should be cancelled.

        This value is consistent only if the loan is a validated request
        (loan.state == ITEM_AT_DESK). If the loan state is different this
        value could represent an other concept.

        :param record: the record metadata.
        """
        from .utils import get_circ_policy
        if record.state == LoanState.ITEM_AT_DESK and \
           'request_expire_date' not in record:
            cipo = get_circ_policy(record)
            duration = cipo.get('pickup_hold_duration')
            library = record.pickup_library
            if cipo.get('allow_requests') and duration and library:
                # the expiration date should be calculated using the pickup
                # library calendar
                trans_date = ciso8601.parse_datetime(record.transaction_date)
                try:
                    expire_date = trans_date + timedelta(days=duration)
                    expire_date = expire_date.replace(
                        hour=23, minute=59, second=00, microsecond=000,
                        tzinfo=None)
                    expire_date = library.next_open(expire_date)
                except LibraryNeverOpen:
                    # 10 days by default ... it's better than place a random
                    # date value
                    default_duration = current_app.config.get(
                        'RERO_ILS_DEFAULT_PICKUP_HOLD_DURATION', 10)
                    expire_date = trans_date + timedelta(days=default_duration)
                    expire_date = expire_date.replace(
                        hour=23, minute=59, second=00, microsecond=000,
                        tzinfo=None)
                # localize the date on the library timezone
                # NOTE: if we create a datetime using `tzinfo`, the conversion
                # to iso format return very precise timestamp (+00:34 for
                # Zurich). But using `localize` method we keep rational +01:00
                # value. This value is well interpreted by browser (+00:34) is
                # not.
                #
                # https://coderedirect.com/questions/421775/python-pytz-
                # timezone-conversion-returns-values-that-differ-from-
                # timezone-offset (Search into response with ~45 points)
                expire_date = library.get_timezone().localize(expire_date)
                record['request_expire_date'] = expire_date.isoformat()
                record['request_start_date'] = datetime.now().isoformat()

    @staticmethod
    def _add_due_soon_date(record):
        """Set the due soon date when the loan is updated if needed.

        :param record: the record metadata.
        """
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

    def pre_commit(self, record):
        """Called before a record is committed."""
        CirculationDatesExtension._add_request_expiration_date(record)
        CirculationDatesExtension._add_due_soon_date(record)
