# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Define relation between records and buckets."""

from invenio_db import db
from invenio_pidstore.models import RecordIdentifier
from invenio_records.models import RecordMetadataBase


class PatronIdentifier(RecordIdentifier):
    """Sequence generator for Patrons identifiers."""

    __tablename__ = "patron_id"
    __mapper_args__ = {"concrete": True}

    recid = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )


class PatronMetadata(db.Model, RecordMetadataBase):
    """Patron record metadata."""

    __tablename__ = "patron_metadata"


class CommunicationChannel:
    """Enum class to list all possible patron communication channels."""

    EMAIL = "email"
    MAIL = "mail"
