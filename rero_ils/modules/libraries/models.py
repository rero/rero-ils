# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Define relation between records and buckets."""

from invenio_db import db
from invenio_pidstore.models import RecordIdentifier
from invenio_records.models import RecordMetadataBase


class LibraryIdentifier(RecordIdentifier):
    """Sequence generator for Library identifiers."""

    __tablename__ = "library_id"
    __mapper_args__ = {"concrete": True}

    recid = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )


class LibraryMetadata(db.Model, RecordMetadataBase):
    """Library record metadata."""

    __tablename__ = "library_metadata"


class LibraryAddressType:
    """Address type for libraries."""

    MAIN_ADDRESS = "main"
    SHIPPING_ADDRESS = "shipping"
    BILLING_ADDRESS = "billing"


class AccountTransferOption:
    """Allowed account transfer option for rollover setting."""

    NO_TRANSFER = "rollover_no_transfer"
    ALLOCATED_AMOUNT = "rollover_allocated_amount"
