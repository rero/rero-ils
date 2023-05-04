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

"""Location serialization."""

from rero_ils.modules.libraries.api import LibrariesSearch
from rero_ils.modules.serializers import CachedDataSerializerMixin, \
    JSONSerializer


class LocationJSONSerializer(JSONSerializer, CachedDataSerializerMixin):
    """Serializer for RERO-ILS `Location` records as JSON."""

    def _postprocess_search_hit(self, hit):
        """Post-process each hit of a search result."""
        metadata = hit.get('metadata', {})

        # Add label for some $ref fields.
        pid = metadata.get('library', {}).get('pid')
        if pid and (resource := self.get_resource(LibrariesSearch(), pid)):
            metadata['library']['code'] = resource.get('code')
            metadata['library']['name'] = resource.get('name')
        super()._postprocess_search_hit(hit)
