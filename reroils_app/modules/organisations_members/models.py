# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017 RERO.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Define relation between organisation and members."""

from __future__ import absolute_import

from invenio_db import db
from invenio_records.models import RecordMetadata
from sqlalchemy_utils.types import UUIDType


class OrganisationsMembersMetadata(db.Model):
    """Relationship between Organisation and Members."""

    __tablename__ = 'organisations_members'

    member_id = db.Column(
        UUIDType,
        db.ForeignKey(RecordMetadata.id),
        primary_key=True,
        nullable=False,
        # NOTE no unique constrain for better future ...
    )
    """Member related with the organisation."""

    member = db.relationship(RecordMetadata, foreign_keys=[member_id])
    """Relationship to the member."""

    organisation_id = db.Column(
        UUIDType,
        db.ForeignKey(RecordMetadata.id),
        primary_key=True,
        nullable=False
    )
    """Organisation related with the member."""

    organisation = db.relationship(
        RecordMetadata, foreign_keys=[organisation_id]
    )
    """It is used by SQLAlchemy for optimistic concurrency control."""

    @classmethod
    def create(cls, organisation, member):
        """Create a new organisationsMember and adds it to the session.

        :param organisation: organisation used to relate with the ``Member``.
        :param member: member used to relate with the ``Organisation``.
        :returns:
            The :class:
            `~reroils_app.modules.organisations_Members.models.OrganisationsMembers`
            object created.
        """
        rb = cls(organisation=organisation, member=member)
        with db.session.begin_nested():
            db.session.add(rb)
        return rb

    @property
    def parent_id(self):
        """Parent id."""
        return self.organisation_id

    @classmethod
    def get_parent(cls):
        """Parent id."""
        return cls.organisation

    @property
    def child_id(self):
        """Parent id."""
        return self.member_id

    @classmethod
    def get_child(cls):
        """Parent id."""
        return cls.member
