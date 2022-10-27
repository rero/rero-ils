# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
# Copyright (C) 2019-2022 UCLouvain
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

"""RERO ILS Record serialization."""

from invenio_records_rest.serializers.response import record_responsify
from invenio_records_rest.serializers.response import \
    search_responsify as _search_responsify

from .base import ACQJSONSerializer, JSONSerializer
from .mixins import CachedDataSerializerMixin, StreamSerializerMixin
from .response import record_responsify_file, search_responsify, \
    search_responsify_file
from .schema import RecordSchemaJSONV1

__all__ = [
    'CachedDataSerializerMixin',
    'StreamSerializerMixin',
    'JSONSerializer',
    'ACQJSONSerializer',
    'RecordSchemaJSONV1',
    'json_v1',
    'json_v1_search',
    'json_v1_response',
    'search_responsify',
    'search_responsify_file',
    'record_responsify_file'
]


json_v1 = JSONSerializer(RecordSchemaJSONV1)
json_v1_search = _search_responsify(json_v1, 'application/json')
json_v1_response = record_responsify(json_v1, 'application/json')
