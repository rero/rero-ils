# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Statistics configuration resource database models."""

from invenio_db import db
from invenio_pidstore.models import RecordIdentifier
from invenio_records.models import RecordMetadataBase


class StatCfgIdentifier(RecordIdentifier):
    """Sequence generator for the statistics configuration identifiers."""

    __tablename__ = "stat_cfg_id"
    __mapper_args__ = {"concrete": True}

    recid = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )


class StatCfgMetadata(db.Model, RecordMetadataBase):
    """Statistics configuration record metadata."""

    __tablename__ = "stat_cfg_metadata"
