# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Define relation between records and buckets."""

from invenio_db import db
from invenio_pidstore.models import RecordIdentifier
from invenio_records.models import RecordMetadataBase


class AcqOrderLineIdentifier(RecordIdentifier):
    """Sequence generator for Acquisition Order Line identifiers."""

    __tablename__ = "acq_order_line_id"
    __mapper_args__ = {"concrete": True}

    recid = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )


class AcqOrderLineMetadata(db.Model, RecordMetadataBase):
    """AcqOrderLine record metadata."""

    __tablename__ = "acq_order_line_metadata"


class AcqOrderLineStatus:
    """Available statuses about an Acquisition Order Line."""

    APPROVED = "approved"
    CANCELLED = "cancelled"
    ORDERED = "ordered"
    RECEIVED = "received"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED_STATUSES = [RECEIVED, PARTIALLY_RECEIVED]


class AcqOrderLineNoteType:
    """Type of acquisition order line note."""

    STAFF = "staff_note"
    VENDOR = "vendor_note"
