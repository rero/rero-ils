# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2022 RERO
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

"""Statistics configuration resource database models."""


from invenio_db import db
from invenio_pidstore.models import RecordIdentifier
from invenio_records.models import RecordMetadataBase


class StatCfgIdentifier(RecordIdentifier):
    """Sequence generator for Stat cfg identifiers."""

    __tablename__ = 'stat_cfg_id'
    __mapper_args__ = {'concrete': True}

    recid = db.Column(
        db.BigInteger().with_variant(db.Integer, 'sqlite'),
        primary_key=True, autoincrement=True,
    )


class StatCfgMetadata(db.Model, RecordMetadataBase):
    """Stat cfg record metadata."""

    __tablename__ = 'stat_cfg_metadata'
