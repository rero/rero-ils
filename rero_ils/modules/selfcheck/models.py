# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Database models for selfcheck terminal."""

from invenio_db import db
from sqlalchemy_utils import IPAddressType


class SelfcheckTerminal(db.Model):
    """Selfcheck terminal model."""

    __tablename__ = "selfcheck_terminals"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(255), unique=True)
    access_token = db.Column(db.String(255), nullable=False)
    organisation_pid = db.Column(db.String(255), nullable=False)
    library_pid = db.Column(db.String(255), nullable=False)
    location_pid = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean(name="active"), default=True)
    last_login_at = db.Column(db.DateTime)
    last_login_ip = db.Column(IPAddressType, nullable=True)
    comments = db.Column(db.Text, nullable=True)

    @classmethod
    def find_terminal(cls, **kwargs):
        """Find selfcheck terminal within the given arguments."""
        query = cls.query
        return query.filter_by(**kwargs).first()
