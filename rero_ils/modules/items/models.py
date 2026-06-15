# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Define relation between records and buckets."""

from invenio_db import db
from invenio_pidstore.models import RecordIdentifier
from invenio_records.models import RecordMetadataBase


class ItemIdentifier(RecordIdentifier):
    """Sequence generator for Item identifiers."""

    __tablename__ = "item_id"
    __mapper_args__ = {"concrete": True}

    recid = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )


class ItemMetadata(db.Model, RecordMetadataBase):
    """Item record metadata."""

    __tablename__ = "item_metadata"


class TypeOfItem:
    """Enum class to list all possible item type."""

    STANDARD = "standard"
    ISSUE = "issue"
    PROVISIONAL = "provisional"


class ItemStatus:
    """Class holding all available circulation item statuses."""

    ON_SHELF = "on_shelf"
    AT_DESK = "at_desk"
    ON_LOAN = "on_loan"
    IN_TRANSIT = "in_transit"
    EXCLUDED = "excluded"
    MISSING = "missing"


class ItemIssueStatus:
    """Enum class to list all possible status of an issue item."""

    DELETED = "deleted"
    EXPECTED = "expected"
    LATE = "late"
    RECEIVED = "received"


class ItemCirculationAction:
    """Enum class to list all possible action about an item."""

    CHECKOUT = "checkout"
    CHECKIN = "checkin"
    REQUEST = "request"
    EXTEND = "extend"


class ItemNoteTypes:
    """Class to list all possible note types."""

    ACQUISITION = "acquisition_note"
    BINDING = "binding_note"
    CHECKIN = "checkin_note"
    CHECKOUT = "checkout_note"
    CONDITION = "condition_note"
    GENERAL = "general_note"
    PATRIMONIAL = "patrimonial_note"
    PROVENANCE = "provenance_note"
    STAFF = "staff_note"

    PUBLIC = [GENERAL, BINDING, PROVENANCE, CONDITION, PATRIMONIAL]

    INVENTORY_LIST_CATEGORY = [
        GENERAL,
        STAFF,
        CHECKIN,
        CHECKOUT,
        ACQUISITION,
        BINDING,
        CONDITION,
        PATRIMONIAL,
        PROVENANCE,
    ]
