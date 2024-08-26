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

"""Patron transaction event serializers."""

from rero_ils.modules.serializers import RecordSchemaJSONV1, search_responsify

from .json import LocationJSONSerializer

__all__ = [
    "json_loc_search",
]


"""JSON serializer."""
_json = LocationJSONSerializer(RecordSchemaJSONV1)
json_loc_search = search_responsify(_json, "application/rero+json")
