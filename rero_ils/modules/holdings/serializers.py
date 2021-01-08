# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
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

"""Holdings serialization."""

from invenio_records_rest.serializers.response import search_responsify

from rero_ils.modules.serializers import JSONSerializer, RecordSchemaJSONV1

from ..item_types.api import ItemType
from ..libraries.api import Library
from ..locations.api import Location


class HoldingsJSONSerializer(JSONSerializer):
    """Mixin serializing records as JSON."""

    def post_process_serialize_search(self, results, pid_fetcher):
        """Post process the search results."""
        records = results.get('hits', {}).get('hits', {})
        for record in records:
            metadata = record.get('metadata', {})
            # Location name
            self._populate_data(metadata, Location, 'location')
            # Library name
            self._populate_data(metadata, Library, 'library')
            # Circulation category
            self._populate_data(metadata, ItemType, 'circulation_category')

        return super(HoldingsJSONSerializer, self)\
            .post_process_serialize_search(results, pid_fetcher)

    @classmethod
    def _populate_data(cls, metadata, resource, field):
        """Populate the current object with the name of resource."""
        field_data = metadata.get(field, {})
        field_pid = field_data.get('pid')
        if field_pid:
            data = resource.get_record_by_pid(field_pid)
            field_data['name'] = data.get('name')


json_holdings = HoldingsJSONSerializer(RecordSchemaJSONV1)
"""JSON v1 serializer."""

json_holdings_search = search_responsify(
    json_holdings, 'application/rero+json')
