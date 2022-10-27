# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
# Copyright (C) 2019-2022 UCLouvain
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

"""Database models for selfcheck terminal."""

from __future__ import absolute_import, print_function

from invenio_db import db
from sqlalchemy_utils import IPAddressType


class SelfcheckTerminal(db.Model):
    """Selfcheck terminal model."""

    __tablename__ = 'selfcheck_terminals'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(db.String(255), unique=True)
    access_token = db.Column(db.String(255), nullable=False)
    organisation_pid = db.Column(db.String(255), nullable=False)
    library_pid = db.Column(db.String(255), nullable=False)
    location_pid = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean(name='active'), default=True)
    last_login_at = db.Column(db.DateTime)
    last_login_ip = db.Column(IPAddressType, nullable=True)
    comments = db.Column(db.Text, nullable=True)

    @classmethod
    def find_terminal(cls, **kwargs):
        """Find selfcheck terminal within the given arguments."""
        query = cls.query
        return query.filter_by(**kwargs).first()
