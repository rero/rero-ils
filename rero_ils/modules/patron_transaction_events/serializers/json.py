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

"""Patron transactions serialization."""

from rero_ils.modules.libraries.api import LibrariesSearch
from rero_ils.modules.locations.api import LocationsSearch
from rero_ils.modules.patron_types.api import PatronTypesSearch
from rero_ils.modules.patrons.api import Patron
from rero_ils.modules.serializers import CachedDataSerializerMixin, \
    JSONSerializer, RecordSchemaJSONV1, search_responsify


class PatronTransactionEventsJSONSerializer(JSONSerializer,
                                            CachedDataSerializerMixin):
    """Serializer for RERO-ILS `PatronTransactionEvent` records as JSON."""

    def _postprocess_search_hit(self, hit):
        """Post-process each hit of a search result."""
        metadata = hit.get('metadata', {})

        # Add label for some $ref fields.
        pid = metadata.get('library', {}).get('pid')
        if pid and (resource := self.get_resource(LibrariesSearch(), pid)):
            metadata['library']['name'] = resource.get('name')

        pid = metadata.get('patron_type', {}).get('pid')
        if pid and (resource := self.get_resource(PatronTypesSearch(), pid)):
            metadata['patron_type']['name'] = resource.get('name')

        pid = metadata.get('operator', {}).get('pid')
        if pid and (resource := self.get_resource(Patron, pid)):
            metadata['operator']['name'] = resource.formatted_name

        super()._postprocess_search_hit(hit)

    def _postprocess_search_aggregations(self, aggregations):
        """Post-process aggregations from a search result."""
        # enrich aggregation hit with some key
        aggrs = aggregations
        JSONSerializer.enrich_bucket_with_data(
            aggrs.get('transaction_library', {}).get('buckets', []),
            LibrariesSearch, 'name'
        )
        JSONSerializer.enrich_bucket_with_data(
            aggrs.get('patron_type', {}).get('buckets', []),
            PatronTypesSearch, 'name'
        )
        JSONSerializer.enrich_bucket_with_data(
            aggrs.get('owning_library', {}).get('buckets', []),
            LibrariesSearch, 'name'
        )
        for loc_bucket in aggrs.get('owning_library', {}).get('buckets', []):
            JSONSerializer.enrich_bucket_with_data(
                loc_bucket.get('owning_location', {}).get('buckets', []),
                LocationsSearch, 'name'
            )

        # add configuration for date-range facets
        aggr = aggregations.get('transaction_date', {})
        JSONSerializer.add_date_range_configuration(aggr)

        super()._postprocess_search_aggregations(aggregations)


_json = PatronTransactionEventsJSONSerializer(RecordSchemaJSONV1)
json_ptre_search = search_responsify(_json, 'application/rero+json')
