# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Define relation between records and buckets."""

from invenio_db import db
from invenio_pidstore.models import RecordIdentifier
from invenio_records.models import RecordMetadataBase


class AcqAccountIdentifier(RecordIdentifier):
    """Sequence generator for acquisition account identifiers."""

    __tablename__ = "acq_account_id"
    __mapper_args__ = {"concrete": True}

    recid = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )


class AcqAccountMetadata(db.Model, RecordMetadataBase):
    """AcqAccount record metadata."""

    __tablename__ = "acq_account_metadata"


class AcqAccountExceedanceType:
    """Type of exceedance about an acquisition account."""

    ENCUMBRANCE = "encumbrance"
    EXPENDITURE = "expenditure"
