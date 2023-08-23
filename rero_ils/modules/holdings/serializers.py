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

"""Holdings serialization."""

from rero_ils.modules.item_types.api import ItemType
from rero_ils.modules.libraries.api import LibrariesSearch
from rero_ils.modules.locations.api import LocationsSearch
from rero_ils.modules.serializers import CachedDataSerializerMixin, \
    JSONSerializer, RecordSchemaJSONV1, search_responsify

from .api import Holding


class HoldingsJSONSerializer(JSONSerializer, CachedDataSerializerMixin):
    """Serializer for RERO-ILS `Holdings` records as JSON."""

    def _postprocess_search_hit(self, hit: dict) -> None:
        """Post-process a search result hit.

        When serializing a holding record, we need to add some keys to the
        search hit :
          * dump related circulation category (itty) information.
          * holdings availability
          * location and library name.
        """
        metadata = hit.get('metadata', {})
        record = Holding.get_record_by_pid(metadata.get('pid'))
        # Circulation category
        circ_category_pid = metadata['circulation_category']['pid']
        circ_category = self.get_resource(ItemType, circ_category_pid)
        metadata['circulation_category'] = circ_category.dumps()
        # Library & location
        if pid := metadata.get('location', {}).get('pid'):
            loc_name = self.get_resource(LocationsSearch(), pid)['name']
            metadata['location']['name'] = loc_name
        if pid := metadata.get('library', {}).get('pid'):
            lib_name = self.get_resource(LibrariesSearch(), pid)['name']
            metadata['library']['name'] = lib_name
        super()._postprocess_search_hit(hit)


_json = HoldingsJSONSerializer(RecordSchemaJSONV1)
json_holdings_search = search_responsify(_json, 'application/rero+json')
