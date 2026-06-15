# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Define relation between records and buckets."""

from invenio_db import db
from invenio_pidstore.models import RecordIdentifier
from invenio_records.models import RecordMetadataBase


class PatronTransactionIdentifier(RecordIdentifier):
    """Sequence generator for Patron Transaction identifiers."""

    __tablename__ = "patron_transaction_id"
    __mapper_args__ = {"concrete": True}

    recid = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )


class PatronTransactionMetadata(db.Model, RecordMetadataBase):
    """PatronTransaction record metadata."""

    __tablename__ = "patron_transaction_metadata"


class PatronTransactionStatus:
    """PatronTransaction status."""

    OPEN = "open"
    CLOSED = "closed"


class PatronTransactionType:
    """PatronTransaction type."""

    DAMAGED = "damaged"
    ILL = "interlibrary_loan"
    LOST = "lost"
    OTHER = "other"
    OVERDUE = "overdue"
    PHOTOCOPY = "photocopy"
    SUBSCRIPTION = "subscription"
