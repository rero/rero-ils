# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Define relation between records and buckets."""

from invenio_db import db
from invenio_pidstore.models import RecordIdentifier
from invenio_records.models import RecordMetadataBase


class AcqReceiptIdentifier(RecordIdentifier):
    """Sequence generator for acquisition receipt identifiers."""

    __tablename__ = "acq_receipt_id"
    __mapper_args__ = {"concrete": True}

    recid = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )


class AcqReceiptMetadata(db.Model, RecordMetadataBase):
    """AcqReceipt record metadata."""

    __tablename__ = "acq_receipt_metadata"


class AcqReceiptNoteType:
    """Type of acquisition receipt note."""

    STAFF = "staff_note"


class AcqReceiptLineCreationStatus:
    """Status following an attempt to create a receipt line."""

    SUCCESS = "success"
    FAILURE = "failure"
