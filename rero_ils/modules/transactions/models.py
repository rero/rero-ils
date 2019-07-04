# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
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

"""Define different types of  transactions."""

from __future__ import absolute_import

import uuid

from invenio_db import db
from invenio_records.models import Timestamp
from sqlalchemy.dialects import postgresql
from sqlalchemy_utils.types import JSONType, UUIDType


class CircTransactions(db.Model, Timestamp):
    """Circulation transactions record."""

    __tablename__ = 'circulation_transactions'

    id = db.Column(UUIDType, primary_key=True, default=uuid.uuid4)
    """Transaction record identifier."""

    json = db.Column(
        db.JSON()
        .with_variant(postgresql.JSONB(none_as_null=True), 'postgresql')
        .with_variant(JSONType(), 'sqlite')
        .with_variant(JSONType(), 'mysql'),
        default=lambda: dict(),
        nullable=True,
    )
    """Store Transaction record metadata in JSON format."""
