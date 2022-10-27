# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
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

from __future__ import absolute_import

from datetime import datetime, timezone

import pytz
from invenio_db import db
from invenio_pidstore.models import RecordIdentifier


class ApiHarvestConfig(RecordIdentifier):
    """Sequence generator for Document identifiers."""

    __tablename__ = 'apiharvester_config'
    __mapper_args__ = {'concrete': True}

    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(255), nullable=False, server_default='')
    name = db.Column(db.String(255), nullable=False)
    mimetype = db.Column(db.String(255), nullable=False)
    size = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    default_last_run = datetime.strptime('1900-1-1', '%Y-%m-%d')
    lastrun = db.Column(db.DateTime, default=pytz.utc.localize(
        default_last_run), nullable=True)

    def save(self):
        """Save object to persistent storage."""
        with db.session.begin_nested():
            db.session.merge(self)

    def update_lastrun(self, new_date=None):
        """Update the 'lastrun' attribute of object to now."""
        self.lastrun = new_date or datetime.now(timezone.utc)
