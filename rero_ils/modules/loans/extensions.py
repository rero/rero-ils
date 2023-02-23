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

"""RERO ILS common record extensions."""


from datetime import datetime, timedelta, timezone

import ciso8601
from flask import current_app
from invenio_records.extensions import RecordExtension

from rero_ils.modules.libraries.exceptions import LibraryNeverOpen
from rero_ils.modules.loans.models import LoanState


class CheckoutLocationExtension(RecordExtension):
    """Manage checkout location for a loan."""

    @staticmethod
    def _add_checkout_location(record):
        """Add the checkout location as a new loan field.

        During the loan life cycle, the transaction location could be updated.
        For example, when a loan is extended, the transaction location pid is
        updated with the location pid where the "extend" operation is done. In
        this case, it's impossible to retrieve the checkout location pid
        without using heavy versioning behavior or external `OperationLog`
        module.

        :param record: the record metadata.
        """
        transaction_pid = record.get('transaction_location_pid')
        if record.get('trigger') == 'checkout' and transaction_pid:
            record['checkout_location_pid'] = transaction_pid

    def pre_commit(self, record):
        """Called before a record is committed."""
        CheckoutLocationExtension._add_checkout_location(record)


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
        value could represent another concept.

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
                    # Ask `duration-1` to get eve to safely use `next_open`
                    expire_date = trans_date + timedelta(days=duration - 1)
                    expire_date = library \
                        .next_open(expire_date) \
                        .astimezone(library.get_timezone()) \
                        .replace(hour=23, minute=59, second=0, microsecond=0)
                except LibraryNeverOpen:
                    # 10 days by default ... it's better than place a random
                    # date value
                    default_duration = current_app.config.get(
                        'RERO_ILS_DEFAULT_PICKUP_HOLD_DURATION', 10)
                    expire_date = trans_date + timedelta(days=default_duration)
                    expire_date = expire_date \
                        .astimezone(library.get_timezone()) \
                        .replace(hour=23, minute=59, second=0, microsecond=0)

                record['request_expire_date'] = expire_date.isoformat()
                record['request_start_date'] = datetime \
                    .now(library.get_timezone()) \
                    .isoformat()

    @staticmethod
    def _add_due_soon_date(record):
        """Set the due soon date when the loan is updated if needed.

        :param record: the record metadata.
        """
        from .utils import get_circ_policy
        if record.state == LoanState.ITEM_ON_LOAN and record.end_date:
            # find the correct policy based on the checkout location.
            circ_policy = get_circ_policy(record, checkout_location=True)
            due_date = ciso8601.parse_datetime(record.end_date).replace(
                tzinfo=timezone.utc)
            if days_before := circ_policy.due_soon_interval_days:
                due_soon = due_date - timedelta(days=days_before)
                due_soon = due_soon.replace(
                    hour=0, minute=0, second=0, microsecond=0)
                record['due_soon_date'] = due_soon.isoformat()

    @staticmethod
    def _add_last_end_date(record):
        """Set the last end date to end date.

        :param record: the record metadata.
        """
        if record.state == LoanState.ITEM_ON_LOAN and record.get('end_date'):
            record['last_end_date'] = record['end_date']

    def pre_commit(self, record):
        """Called before a record is committed."""
        CirculationDatesExtension._add_request_expiration_date(record)
        CirculationDatesExtension._add_due_soon_date(record)
        CirculationDatesExtension._add_last_end_date(record)
