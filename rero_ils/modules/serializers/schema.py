# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
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

"""RERO ILS Record schema for serialization."""
from invenio_records_rest.schemas import \
    RecordSchemaJSONV1 as _RecordSchemaJSONV1
from marshmallow import fields


class RecordSchemaJSONV1(_RecordSchemaJSONV1):
    """Schema for records RERO ILS in JSON.

    Add permissions & explanation fields.
    """

    permissions = fields.Raw()
    explanation = fields.Raw()
