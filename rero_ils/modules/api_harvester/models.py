# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2024 RERO
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Define relation between records and buckets."""

from datetime import datetime, timezone
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
    lastrun = db.Column(
        db.DateTime, default=datetime(year=1900, month=1, day=1), nullable=True
    )

    def save(self):
        """Save object to persistent storage."""
        with db.session.begin_nested():
            db.session.merge(self)

    def update_lastrun(self, new_date=None):
        """Update the 'lastrun' attribute of object to now."""
        self.lastrun = new_date or datetime.now(timezone.utc)
        self.save()
        return self.lastrun
