# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Define relation between records and buckets."""

from invenio_db import db
from invenio_pidstore.models import RecordIdentifier
from invenio_records.models import RecordMetadataBase


class AcqReceiptLineIdentifier(RecordIdentifier):
    """Sequence generator for acquisition receipt line identifiers."""

    __tablename__ = "acq_receipt_line_id"
    __mapper_args__ = {"concrete": True}

    recid = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )


class AcqReceiptLineMetadata(db.Model, RecordMetadataBase):
    """AcqReceiptLine record metadata."""

    __tablename__ = "acq_receipt_line_metadata"


class AcqReceiptLineNoteType:
    """Type of acquisition receipt line note."""

    STAFF = "staff_note"
    RECEIPT = "receipt_note"
