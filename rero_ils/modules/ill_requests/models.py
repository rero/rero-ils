# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Define relation between records and buckets."""

from invenio_db import db
from invenio_pidstore.models import RecordIdentifier
from invenio_records.models import RecordMetadataBase


class ILLRequestIdentifier(RecordIdentifier):
    """Sequence generator for ILLRequest identifiers."""

    __tablename__ = "ill_request_id"
    __mapper_args__ = {"concrete": True}

    recid = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )


class ILLRequestMetadata(db.Model, RecordMetadataBase):
    """ILLRequest record metadata."""

    __tablename__ = "ill_request_metadata"


class ILLRequestStatus:
    """Available status for an ILL request."""

    PENDING = "pending"
    VALIDATED = "validated"
    DENIED = "denied"
    CLOSED = "closed"


class ILLRequestNoteStatus:
    """Available note status for an ILL request."""

    PUBLIC_NOTE = "public_note"
    STAFF_NOTE = "staff_note"
