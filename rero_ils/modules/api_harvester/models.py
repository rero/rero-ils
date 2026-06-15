# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Define relation between records and buckets."""

from datetime import UTC, datetime
from enum import Enum

from invenio_db import db


class HarvestActionType(Enum):
    """Harvest action types."""

    DELETED = "DELETED"
    UPDATED = "UPDATED"
    CREATED = "CREATED"
    NOTSET = "NOTSET"


class ApiHarvestConfig(db.Model):
    """Represents a ApiHarvestConfig record."""

    __tablename__ = "apiharvester_config"

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(255), nullable=False, server_default="")
    name = db.Column(db.String(255), nullable=False)
    classname = db.Column(db.String(255), nullable=False)
    code = db.Column(db.Text, nullable=True)
    lastrun = db.Column(db.DateTime, default=datetime(year=1900, month=1, day=1, tzinfo=UTC), nullable=True)

    def save(self):
        """Save object to persistent storage."""
        with db.session.begin_nested():
            db.session.merge(self)

    def update_lastrun(self, new_date=None):
        """Update the 'lastrun' attribute of object to now."""
        self.lastrun = new_date or datetime.now(UTC)
        self.save()
        return self.lastrun
