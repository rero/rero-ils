# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Define relation between records and buckets."""

from invenio_db import db
from invenio_pidstore.models import RecordIdentifier
from invenio_records.models import RecordMetadataBase


class NotificationIdentifier(RecordIdentifier):
    """Sequence generator for Notifications identifiers."""

    __tablename__ = "notification_id"
    __mapper_args__ = {"concrete": True}

    recid = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )


class NotificationMetadata(db.Model, RecordMetadataBase):
    """Notification record metadata."""

    __tablename__ = "notifications_metadata"


class NotificationType:
    """Types of notifications.

    - RECALL            : when a new request is done on a loaned item.
    - AT_DESK           : when a requested item arrives at desk ; sent to the
                          transaction library. (possible configurable delay)
    - AVAILABILITY      : when a requested item arrives at desk  sent to the
                          patron. (possible configurable delay)
    - REQUEST           : created when the item is at desk and a request
                          occurs.
    - BOOKING           : when the item is checked in and have a request.
    - TRANSIT_NOTICE    : when an item is sent to the owning location/library
    - DUE_SOON          : when the loaned item is about to expire.
    - OVERDUE           : when the loaned item is expired.
    - ACQUISITION_ORDER : when an acquisition order is sent to a vendor.
    - CLAIM_ISSUE       : when a claim is sent to a vendor about a serial issue
    - AUTO_EXTEND       : when a loan has been automatically extended by the
                          system.
    """

    ACQUISITION_ORDER = "acquisition_order"
    AT_DESK = "at_desk"
    AUTO_EXTEND = "auto_extend"
    AVAILABILITY = "availability"
    BOOKING = "booking"
    CLAIM_ISSUE = "claim_issue"
    DUE_SOON = "due_soon"
    OVERDUE = "overdue"
    RECALL = "recall"
    REQUEST = "request"
    TRANSIT_NOTICE = "transit_notice"

    # All notification types
    ALL_NOTIFICATIONS = [
        AT_DESK,
        AVAILABILITY,
        DUE_SOON,
        OVERDUE,
        RECALL,
        TRANSIT_NOTICE,
        REQUEST,
        BOOKING,
    ]
    # Notification related to cipo reminders.
    REMINDERS_NOTIFICATIONS = [DUE_SOON, OVERDUE]
    # Notification to send to a library (not to a patron)
    INTERNAL_NOTIFICATIONS = [AT_DESK, BOOKING, REQUEST, TRANSIT_NOTICE]

    # Notification related to circulation modules
    CIRCULATION_NOTIFICATIONS = [
        AT_DESK,
        AUTO_EXTEND,
        AVAILABILITY,
        DUE_SOON,
        OVERDUE,
        RECALL,
        TRANSIT_NOTICE,
        REQUEST,
        BOOKING,
    ]


class NotificationStatus:
    """Notification status."""

    DONE = "done"
    CREATED = "created"
    CANCELLED = "cancelled"


class NotificationChannel:
    """Notification channels."""

    MAIL = "mail"
    EMAIL = "email"
    PATRON_SETTING = "patron_setting"


class RecipientType:
    """Notification recipient type."""

    TO = "to"
    CC = "cc"
    BCC = "bcc"
    REPLY_TO = "reply_to"
