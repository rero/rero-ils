# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Define relation between records and buckets."""

from invenio_db import db
from invenio_pidstore.models import RecordIdentifier
from invenio_records.models import RecordMetadataBase


class VendorIdentifier(RecordIdentifier):
    """Sequence generator for Vendor identifiers."""

    __tablename__ = "vendor_id"
    __mapper_args__ = {"concrete": True}

    recid = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )


class VendorMetadata(db.Model, RecordMetadataBase):
    """Vendor record metadata."""

    __tablename__ = "vendor_metadata"


class VendorContactType:
    """Type of vendor contact."""

    DEFAULT = "default"
    ORDER = "order"
    SERIAL = "serial"


class VendorNoteType:
    """Type of vendor note."""

    ORDER = "order_note"
    CLAIM = "claim_note"
    RETURN = "return_note"
    INVOICE = "invoice_note"
    PAYMENT = "payment_note"
    RECEIPT = "receipt_note"
    CREDIT = "credit_note"
    STAFF = "staff_note"
    GENERAL = "general_note"
