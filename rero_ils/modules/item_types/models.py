# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Define relation between records and buckets."""

from invenio_db import db
from invenio_pidstore.models import RecordIdentifier
from invenio_records.models import RecordMetadataBase


class ItemTypeIdentifier(RecordIdentifier):
    """Sequence generator for ItemType identifiers."""

    __tablename__ = "item_type_id"
    __mapper_args__ = {"concrete": True}

    recid = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )


class ItemTypeMetadata(db.Model, RecordMetadataBase):
    """ItemType record metadata."""

    __tablename__ = "item_type_metadata"
