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

"""ILL Request serialization."""

from invenio_records_rest.serializers.response import record_responsify

from rero_ils.modules.libraries.api import LibrariesSearch
from rero_ils.modules.locations.api import LocationsSearch
from rero_ils.modules.serializers import CachedDataSerializerMixin, \
    JSONSerializer, RecordSchemaJSONV1, search_responsify


class ILLRequestJSONSerializer(JSONSerializer, CachedDataSerializerMixin):
    """Serializer for RERO-ILS `ILLRequest` records as JSON."""

    def _postprocess_search_hit(self, hit: dict) -> None:
        """Post-process each hit of a search result."""
        metadata = hit.get('metadata', {})
        if pid := metadata.get('pickup_location', {}).get('pid'):
            location = self.get_resource(LocationsSearch(), pid)
            pickup_name = location.get('ill_pickup_name', location.get('name'))
            metadata['pickup_location']['name'] = pickup_name
        super()._postprocess_search_hit(hit)

    def _postprocess_search_aggregations(self, aggregations: dict) -> None:
        """Post-process aggregations from a search result."""
        JSONSerializer.enrich_bucket_with_data(
            aggregations.get('library', {}).get('buckets', []),
            LibrariesSearch, 'name'
        )
        super()._postprocess_search_aggregations(aggregations)


_json = ILLRequestJSONSerializer(RecordSchemaJSONV1)
json_ill_request_search = search_responsify(_json, 'application/rero+json')
json_ill_request_response = record_responsify(_json, 'application/rero+json')
