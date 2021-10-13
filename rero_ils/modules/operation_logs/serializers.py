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

"""Operation Logs serialization."""

from invenio_records_rest.serializers.response import search_responsify

from rero_ils.modules.locations.api import Location
from rero_ils.modules.serializers import JSONSerializer, RecordSchemaJSONV1

from ..libraries.api import Library


class OperationLogsJSONSerializer(JSONSerializer):
    """Mixin serializing records as JSON."""

    # Cache for locations and libraries
    _cache = {}

    def post_process_serialize_search(self, results, pid_fetcher):
        """Post process the search results."""
        records = results.get('hits', {}).get('hits', [])
        for record in records:
            metadata = record.get('metadata', {})
            if 'loan' in metadata:
                transaction_location = metadata.get('loan', {})\
                    .get('transaction_location', {})
                transaction_location_pid = transaction_location.get('pid')
                if transaction_location_pid:
                    transaction_library = self._get_library_by_location(
                        transaction_location_pid)
                    if transaction_library:
                        transaction_location['library'] = transaction_library
                pickup_location = metadata.get('loan', {})\
                    .get('pickup_location', {})
                pickup_location_pid = pickup_location.get('pid')
                if pickup_location_pid:
                    pickup_library = self._get_library_by_location(
                        pickup_location_pid)
                    if pickup_library:
                        pickup_location['library'] = pickup_library

        return super(OperationLogsJSONSerializer, self)\
            .post_process_serialize_search(results, pid_fetcher)

    def _get_library_by_location(self, location_pid):
        """Get library by location pid.

        :param: str location_pid: Location Pid
        :returns: Library informations
        """
        # --- Location
        location_key = f"location-{location_pid}"
        if location_key not in self._cache:
            location = Location.get_record_by_pid(location_pid)
            self._cache.setdefault(location_key, location)
        else:
            location = self._cache.get(location_key)
        # --- Library
        library_pid = location.library_pid
        library_key = f"library-{library_pid}"
        if library_key not in self._cache:
            library = Library.get_record_by_pid(library_pid)
            self._cache.setdefault(library_key, library)
        else:
            library = self._cache.get(library_key)
        if library:
            return {
                'name': library['name'],
                'pid': library['pid']
            }


json_operation_logs = OperationLogsJSONSerializer(RecordSchemaJSONV1)
"""JSON v1 serializer."""

json_operation_logs_search = search_responsify(
    json_operation_logs, 'application/rero+json')
