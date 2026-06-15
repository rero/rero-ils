# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Define relation between records and buckets."""

from enum import Enum

from invenio_db import db
from invenio_pidstore.models import RecordIdentifier
from invenio_records.models import RecordMetadataBase


class DocumentIdentifier(RecordIdentifier):
    """Sequence generator for Document identifiers."""

    __tablename__ = "document_id"
    __mapper_args__ = {"concrete": True}

    recid = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )


class DocumentMetadata(db.Model, RecordMetadataBase):
    """Document record metadata."""

    __tablename__ = "document_metadata"


class DocumentFictionType(Enum):
    """Document fiction types."""

    Fiction = "fiction"
    NonFiction = "non_fiction"
    Unspecified = "unspecified"
