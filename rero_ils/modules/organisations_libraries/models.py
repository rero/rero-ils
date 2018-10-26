# -*- coding: utf-8 -*-
#
# This file is part of RERO ILS.
# Copyright (C) 2017 RERO.
#
# RERO ILS is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# RERO ILS is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RERO ILS; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Define relation between organisation and libraries."""

from __future__ import absolute_import

from invenio_db import db
from invenio_records.models import RecordMetadata
from sqlalchemy_utils.types import UUIDType


class OrganisationsLibrariesMetadata(db.Model):
    """Relationship between Organisation and Libraries."""

    __tablename__ = 'organisations_libraries'

    library_id = db.Column(
        UUIDType,
        db.ForeignKey(RecordMetadata.id),
        primary_key=True,
        nullable=False,
        # NOTE no unique constrain for better future ...
    )
    """Library related with the organisation."""

    library = db.relationship(RecordMetadata, foreign_keys=[library_id])
    """Relationship to the library."""

    organisation_id = db.Column(
        UUIDType,
        db.ForeignKey(RecordMetadata.id),
        primary_key=True,
        nullable=False
    )
    """Organisation related with the library."""

    organisation = db.relationship(
        RecordMetadata, foreign_keys=[organisation_id]
    )
    """It is used by SQLAlchemy for optimistic concurrency control."""

    @classmethod
    def create(cls, organisation, library):
        """Create a new organisationsLibrary and adds it to the session.

        :param organisation: organisation used to relate with the ``Library``.
        :param library: library used to relate with the ``Organisation``.
        :returns:
            The :class:
            `~rero_ils.modules.organisations_Libraries.models.OrganisationsLibraries`
            object created.
        """
        rb = cls(organisation=organisation, library=library)
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
        return self.library_id

    @classmethod
    def get_child(cls):
        """Parent id."""
        return cls.library
