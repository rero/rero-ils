# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Statistics resource database models."""

from invenio_db import db
from invenio_pidstore.models import RecordIdentifier
from invenio_records.models import RecordMetadataBase


class StatIdentifier(RecordIdentifier):
    """Sequence generator for Stat identifiers."""

    __tablename__ = "stat_id"
    __mapper_args__ = {"concrete": True}

    recid = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )


class StatMetadata(db.Model, RecordMetadataBase):
    """Stat record metadata."""

    __tablename__ = "stat_metadata"


class StatType:
    """Type of statistics record."""

    BILLING = "billing"
    LIBRARIAN = "librarian"
    REPORT = "report"
