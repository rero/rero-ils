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

"""Operation Logs serialization."""
from rero_ils.modules.libraries.api import LibrariesSearch
from rero_ils.modules.locations.api import LocationsSearch
from rero_ils.modules.serializers import CachedDataSerializerMixin, \
    JSONSerializer, RecordSchemaJSONV1, search_responsify


class OperationLogsJSONSerializer(JSONSerializer, CachedDataSerializerMixin):
    """Serializer for RERO-ILS `OperationLog` records as JSON."""

    def _postprocess_search_hit(self, hit: dict) -> None:
        """Post-process each hit of a search result."""
        # add library name if the library entry exists.
        if library := hit.get('metadata', {}).get('library'):
            library['name'] = self.get_resource(
                LibrariesSearch(), library.get('value'))['name']
        if 'loan' in (metadata := hit.get('metadata', {})):
            # enrich `transaction_location` and `pickup_location` fields with
            # related library information
            trans_loc_field = metadata['loan'].get('transaction_location', {})
            self._enrich_with_library_info(trans_loc_field)
            pickup_loc_field = metadata['loan'].get('pickup_location', {})
            self._enrich_with_library_info(pickup_loc_field)
        super()._postprocess_search_hit(hit)

    def _enrich_with_library_info(self, field):
        """Enrich a location field with related library information.

        :param field: the dictionary field to enrich. This dictionary should
                      contain the location pid.
        """
        if location := self.get_resource(LocationsSearch(), field.get('pid')):
            lib_pid = location.get('library', {}).get('pid')
            if library := self.get_resource(LibrariesSearch(), lib_pid):
                field['library'] = {
                    'pid': library['pid'],
                    'name': library['name']
                }


_json = OperationLogsJSONSerializer(RecordSchemaJSONV1)
json_oplogs_search = search_responsify(_json, 'application/rero+json')
