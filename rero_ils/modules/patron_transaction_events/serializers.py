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

"""Patron transactions serialization."""

from invenio_records_rest.serializers.response import search_responsify

from rero_ils.modules.libraries.api import LibrariesSearch
from rero_ils.modules.serializers import CachedDataSerializerMixin, \
    JSONSerializer, RecordSchemaJSONV1


class PatronTransactionEventsJSONSerializer(JSONSerializer,
                                            CachedDataSerializerMixin):
    """Serializer for RERO-ILS `PatronTransactionEvent` records as JSON."""

    def _postprocess_search_hit(self, hit: dict) -> None:
        """Post-process each hit of a search result."""
        metadata = hit.get('metadata', {})
        lib_pid = metadata.get('library', {}).get('pid')
        if lib := self.get_resource(LibrariesSearch(), lib_pid):
            metadata['library']['name'] = lib.get('name')
        super()._postprocess_search_hit(hit)


_json = PatronTransactionEventsJSONSerializer(RecordSchemaJSONV1)
json_ptre_search = search_responsify(_json, 'application/rero+json')
