# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
# Copyright (C) 2021 UCLouvain
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

"""Database models for selfcheck user."""

from __future__ import absolute_import, print_function

from invenio_db import db

selfcheck_userrole = db.Table(
    'selfcheck_userrole',
    db.Column('user_id', db.Integer(), db.ForeignKey(
        'selfcheck_accounts.id', name='fk_selfcheck_userrole_user_id')),
    db.Column('role_id', db.Integer(), db.ForeignKey(
        'accounts_role.id', name='fk_selfcheck_userrole_role_id')),
)
"""Relationship between users and roles."""


class SelfcheckUser(db.Model):
    """Selfcheck user model."""

    __tablename__ = 'selfcheck_accounts'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(db.String(255), unique=True)
    access_token = db.Column(db.String(255), nullable=False)
    organisation_pid = db.Column(db.String(255), nullable=False)
    location_pid = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean(name='active'))
    last_login_at = db.Column(db.DateTime)

    roles = db.relationship('Role', secondary=selfcheck_userrole,
                            backref=db.backref('selfcheck_users',
                                               lazy='dynamic'))
