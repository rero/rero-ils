# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
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

"""Notification record extensions."""

from invenio_records.extensions import RecordExtension

from .models import NotificationType


class NotificationSubclassExtension(RecordExtension):
    """Notification extension for choosing the best notification subclass.

    `Notification` is a parent abstract class. To process the notification, we
    need to find its context and to find it, we need to cast any Notification
    instance to the corresponding `Notification` subclass. The subclass
    selection is done by analyzing the requested `notification_type` attribute.
    """

    @staticmethod
    def _get_circulation_subclass(record):
        """Get the Notification subclass to use based on record data."""
        from .api import Notification
        from .subclasses.acq_order import AcquisitionOrderNotification
        from .subclasses.at_desk import AtDeskCirculationNotification
        from .subclasses.availability import \
            AvailabilityCirculationNotification
        from .subclasses.booking import BookingCirculationNotification
        from .subclasses.claim_issue import ClaimSerialIssueNotification
        from .subclasses.recall import RecallCirculationNotification
        from .subclasses.reminder import ReminderCirculationNotification
        from .subclasses.request import RequestCirculationNotification
        from .subclasses.transit import TransitCirculationNotification
        mapping = {
            NotificationType.AVAILABILITY: AvailabilityCirculationNotification,
            NotificationType.AT_DESK: AtDeskCirculationNotification,
            NotificationType.BOOKING: BookingCirculationNotification,
            NotificationType.DUE_SOON: ReminderCirculationNotification,
            NotificationType.OVERDUE: ReminderCirculationNotification,
            NotificationType.RECALL: RecallCirculationNotification,
            NotificationType.REQUEST: RequestCirculationNotification,
            NotificationType.TRANSIT_NOTICE: TransitCirculationNotification,
            NotificationType.ACQUISITION_ORDER: AcquisitionOrderNotification,
            NotificationType.CLAIM_ISSUE: ClaimSerialIssueNotification
        }
        try:
            return mapping[record.type]
        except KeyError:
            return Notification

    def post_init(self, record, data, model=None, **kwargs):
        """Called after a record is initialized."""
        cls = NotificationSubclassExtension._get_circulation_subclass(record)
        record.__class__ = cls
