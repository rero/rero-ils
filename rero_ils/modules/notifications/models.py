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

"""Define relation between records and buckets."""

from __future__ import absolute_import

from invenio_db import db
from invenio_pidstore.models import RecordIdentifier
from invenio_records.models import RecordMetadataBase


class NotificationIdentifier(RecordIdentifier):
    """Sequence generator for Notifications identifiers."""

    __tablename__ = 'notification_id'
    __mapper_args__ = {'concrete': True}

    recid = db.Column(
        db.BigInteger().with_variant(db.Integer, 'sqlite'),
        primary_key=True, autoincrement=True,
    )


class NotificationMetadata(db.Model, RecordMetadataBase):
    """Notification record metadata."""

    __tablename__ = 'notifications_metadata'


class NotificationType:
    """Types of notifications."""

    # when a new request is done on a loaned item
    RECALL = 'recall'

    # when a requested item arrive at desk
    AVAILABILITY = 'availability'

    # when the loaned item is about to expire
    # NOTE : process by a recurrent task
    DUE_SOON = 'due_soon'

    # when the loaned item is expired
    # NOTE : process by a recurrent task
    OVERDUE = 'overdue'

    # when an item is sent to the owning location/library
    TRANSIT_NOTICE = 'transit_notice'

    # when the item is at desk and a request occurs
    # NOTE : can have a delay
    REQUEST = 'request'

    # when the item is checked in an have a request
    BOOKING = 'booking'

    ALL_NOTIFICATIONS = [
        AVAILABILITY,
        DUE_SOON,
        OVERDUE, RECALL,
        TRANSIT_NOTICE,
        REQUEST,
        BOOKING
    ]

    # Notification related to cipo reminders.
    REMINDERS_NOTIFICATIONS = [
        DUE_SOON,
        OVERDUE
    ]

    # Notification to send to a library (not to a patron)
    INTERNAL_NOTIFICATIONS = [
        BOOKING,
        REQUEST,
        TRANSIT_NOTICE
    ]


class NotificationChannel:
    """Notification channels."""

    MAIL = 'mail'
    EMAIL = 'email'
    PATRON_SETTING = 'patron_setting'
