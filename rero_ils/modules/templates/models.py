# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Define relation between records and buckets."""

from invenio_db import db
from invenio_pidstore.models import RecordIdentifier
from invenio_records.models import RecordMetadataBase


class TemplateIdentifier(RecordIdentifier):
    """Sequence generator for templates identifiers."""

    __tablename__ = "template_id"
    __mapper_args__ = {"concrete": True}

    recid = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )


class TemplateMetadata(db.Model, RecordMetadataBase):
    """Template record metadata."""

    __tablename__ = "template_metadata"


class TemplateVisibility:
    """Class to handle different template visibilities."""

    PUBLIC = "public"
    PRIVATE = "private"
