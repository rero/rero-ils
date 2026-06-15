# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Define relation between records and buckets."""

from invenio_db import db
from invenio_pidstore.models import RecordIdentifier
from invenio_records.models import RecordMetadataBase


class PatronTransactionEventIdentifier(RecordIdentifier):
    """Sequence generator for PatronTransactionEvent identifiers."""

    __tablename__ = "patron_transaction_event_id"
    __mapper_args__ = {"concrete": True}

    recid = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )


class PatronTransactionEventMetadata(db.Model, RecordMetadataBase):
    """PatronTransactionEvent record metadata."""

    __tablename__ = "patron_transaction_event_metadata"


class PatronTransactionEventType:
    """Type of PatronTransactionEvent."""

    FEE = "fee"
    PAYMENT = "payment"
    DISPUTE = "dispute"
    CANCEL = "cancel"
