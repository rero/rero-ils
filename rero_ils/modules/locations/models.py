# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Define relation between records and buckets."""

from invenio_db import db
from invenio_pidstore.models import RecordIdentifier
from invenio_records.models import RecordMetadataBase


class LocationIdentifier(RecordIdentifier):
    """Sequence generator for Location identifiers."""

    __tablename__ = "location_id"
    __mapper_args__ = {"concrete": True}

    recid = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )


class LocationMetadata(db.Model, RecordMetadataBase):
    """Location record metadata."""

    __tablename__ = "location_metadata"
