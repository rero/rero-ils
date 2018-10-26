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

"""Define relation between libraries and locations."""

from __future__ import absolute_import

from invenio_db import db
from invenio_records.models import RecordMetadata
from sqlalchemy_utils.types import UUIDType


class LibrariesLocationsMetadata(db.Model):
    """Relationship between Libraries and Locations."""

    __tablename__ = 'libraries_locations'

    location_id = db.Column(
        UUIDType,
        db.ForeignKey(RecordMetadata.id),
        primary_key=True,
        nullable=False,
        # NOTE no unique constrain for better future ...
    )
    """Location related with the library."""

    location = db.relationship(RecordMetadata, foreign_keys=[location_id])
    """Relationship to the location."""

    library_id = db.Column(
        UUIDType,
        db.ForeignKey(RecordMetadata.id),
        primary_key=True,
        nullable=False
    )
    """Library related with the location."""

    library = db.relationship(
        RecordMetadata, foreign_keys=[library_id]
    )
    """It is used by SQLAlchemy for optimistic concurrency control."""

    @classmethod
    def create(cls, library, location):
        """Create a new libraryLocation and adds it to the session.

        :param library: library used to relate with the ``Location``.
        :param location: library used to relate with the ``Library``.
        :returns:
            The :class:
            `~rero_ils.modules.libraries_locations.models.LibrariesLocations`
            object created.
        """
        rb = cls(library=library, location=location)
        with db.session.begin_nested():
            db.session.add(rb)
        return rb

    @property
    def parent_id(self):
        """Parent id."""
        return self.library_id

    @classmethod
    def get_parent(cls):
        """Parent id."""
        return cls.library

    @property
    def child_id(self):
        """Parent id."""
        return self.location_id

    @classmethod
    def get_child(cls):
        """Parent id."""
        return cls.location
