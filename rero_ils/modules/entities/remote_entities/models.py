# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Define relation between records and buckets."""

from invenio_db import db
from invenio_pidstore.models import RecordIdentifier
from invenio_records.models import RecordMetadataBase


class RemoteEntityIdentifier(RecordIdentifier):
    """Sequence generator for `Remote Entity` identifiers."""

    __tablename__ = "remote_entity_id"
    __mapper_args__ = {"concrete": True}

    recid = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )


class RemoteEntityMetadata(db.Model, RecordMetadataBase):
    """Remote Entity record metadata."""

    __tablename__ = "remote_entity_metadata"


class EntityUpdateAction:
    """Class holding all available agent record creation actions."""

    REPLACE = "replace"
    UPTODATE = "uptodate"
    ERROR = "error"
