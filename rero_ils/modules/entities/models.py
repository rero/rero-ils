# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
# Copyright (C) 2019-2023 UCLouvain
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

from invenio_db import db
from invenio_pidstore.models import RecordIdentifier
from invenio_records.models import RecordMetadataBase


class EntityIdentifier(RecordIdentifier):
    """Sequence generator for `Entity` identifiers."""

    __tablename__ = 'entity_id'
    __mapper_args__ = {'concrete': True}

    recid = db.Column(
        db.BigInteger().with_variant(db.Integer, 'sqlite'),
        primary_key=True,
        autoincrement=True,
    )


class EntityMetadata(db.Model, RecordMetadataBase):
    """Entity record metadata."""

    __tablename__ = 'entity_metadata'


class EntityType:
    """Class holding all available entity types."""

    AGENT = 'bf:Agent'
    CONCEPT = 'bf:Concept'
    ORGANISATION = 'bf:Organisation'
    PERSON = 'bf:Person'
    PLACE = 'bf:Place'
    TEMPORAL = 'bf:Temporal'
    TOPIC = 'bf:Topic'
    WORK = 'bf:Work'


class EntityUpdateAction:
    """Class holding all available agent record creation actions."""

    REPLACE = 'replace'
    UPTODATE = 'uptodate'
    ERROR = 'error'
