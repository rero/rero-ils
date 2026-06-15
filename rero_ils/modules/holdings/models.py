# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Define relation between records and buckets."""

from invenio_db import db
from invenio_pidstore.models import RecordIdentifier
from invenio_records.models import RecordMetadataBase


class HoldingIdentifier(RecordIdentifier):
    """Sequence generator for holdings identifiers."""

    __tablename__ = "holding_id"
    __mapper_args__ = {"concrete": True}

    recid = db.Column(
        db.BigInteger().with_variant(db.Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )


class HoldingMetadata(db.Model, RecordMetadataBase):
    """Holding record metadata."""

    __tablename__ = "holding_metadata"


class HoldingTypes:
    """Class to list all possible holding types."""

    ELECTRONIC = "electronic"
    SERIAL = "serial"
    STANDARD = "standard"


class HoldingNoteTypes:
    """Class to list all holdings possible note types."""

    GENERAL = "general_note"
    STAFF = "staff_note"
    CONSERVATION = "conservation_note"
    RECEPTION = "reception_note"
    CLAIM = "claim_note"
    ROUTING = "routing_note"
    BINDING = "binding_note"
    ACQUISITION = "acquisition_note"

    # TODO: Add any of the above items to the array
    # to display them on the interface
    PUBLIC = []


class HoldingCirculationAction:
    """Enum class to list all possible action about an holding."""

    REQUEST = "request"
