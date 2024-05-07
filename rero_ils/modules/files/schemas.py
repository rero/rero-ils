# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2024 RERO
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

"""Files support for the RERO invenio instances."""

from invenio_records_resources.services.records.schema import BaseRecordSchema
from marshmallow import Schema, fields, pre_load
from marshmallow_utils.fields import SanitizedUnicode


class MetadataSchema(Schema):
    """Record metadata schema class."""

    collections = fields.List(SanitizedUnicode())
    library = fields.Dict(required=True)
    document = fields.Dict(required=True)
    n_files = fields.Int(dump_only=True)
    file_size = fields.Int(dump_only=True)

    @pre_load
    def remove_fields(self, data, **kwargs):
        """Removes computed fields.

        :param data: Dict of record data.
        :returns: Modified data.
        """
        data.pop('n_files', None)
        data.pop('file_size', None)
        return data


class RecordSchema(BaseRecordSchema):
    """Service schema for subjects."""

    metadata = fields.Nested(MetadataSchema)
