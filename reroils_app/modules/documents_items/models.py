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

"""Define relation between documents and items."""

from __future__ import absolute_import

from invenio_db import db
from invenio_records.models import RecordMetadata
from sqlalchemy_utils.types import UUIDType


class DocumentsItemsMetadata(db.Model):
    """Relationship between Documents and Items."""

    __tablename__ = 'documents_items'

    item_id = db.Column(
        UUIDType,
        db.ForeignKey(RecordMetadata.id),
        primary_key=True,
        nullable=False,
        # NOTE no unique constrain for better future ...
    )
    """Item related with the document."""

    item = db.relationship(RecordMetadata, foreign_keys=[item_id])
    """Relationship to the item."""

    document_id = db.Column(
        UUIDType,
        db.ForeignKey(RecordMetadata.id),
        primary_key=True,
        nullable=False
    )
    """Document related with the item."""

    document = db.relationship(RecordMetadata, foreign_keys=[document_id])
    """It is used by SQLAlchemy for optimistic concurrency control."""

    @classmethod
    def create(cls, document, item):
        """Create a new DocumentsItem and adds it to the session.

        :param document: Document used to relate with the ``Item``.
        :param item: Item used to relate with the ``Record``.
        :returns:
            The :class:
            `~reroils_app.modules.documents_items.models.RecordsItems`
            object created.
        """
        rb = cls(document=document, item=item)
        with db.session.begin_nested():
            db.session.add(rb)
        return rb

    @property
    def parent_id(self):
        """Parent id."""
        return self.document_id

    @classmethod
    def get_parent(cls):
        """Parent id."""
        return cls.document

    @property
    def child_id(self):
        """Parent id."""
        return self.item_id

    @classmethod
    def get_child(cls):
        """Parent id."""
        return cls.item
