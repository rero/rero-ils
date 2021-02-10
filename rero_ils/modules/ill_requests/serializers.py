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

"""ILL Request serialization."""

from invenio_records_rest.serializers.response import search_responsify

from ..libraries.api import Library
from ..locations.api import Location
from ..serializers import JSONSerializer, RecordSchemaJSONV1


class ILLRequestJSONSerializer(JSONSerializer):
    """Mixin serializing records as JSON."""

    def post_process_serialize_search(self, results, pid_fetcher):
        """Post process the search results."""
        aggrs = results.get('aggregations', {})
        # replace the library pid by the library name for faceting
        for lib_term in aggrs.get('library', {}).get('buckets', []):
            pid = lib_term.get('key')
            lib_term['name'] = Library.get_record_by_pid(pid).get('name')
        # Populate record
        records = results.get('hits', {}).get('hits', {})
        for record in records:
            metadata = record.get('metadata', {})
            location_pid = metadata.get('pickup_location', {}).get('pid')
            location = Location.get_record_by_pid(location_pid)
            pickup_name = location.get('pickup_name', location.get('name'))
            metadata['pickup_location']['name'] = pickup_name

        return super().post_process_serialize_search(results, pid_fetcher)


json_ill_request = ILLRequestJSONSerializer(RecordSchemaJSONV1)
json_ill_request_search = search_responsify(json_ill_request,
                                            'application/rero+json')
