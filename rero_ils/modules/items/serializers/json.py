# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
# Copyright (C) 2020-2023 UCLouvain
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

"""RERO Item JSON serialization."""

from rero_ils.modules.documents.api import DocumentsSearch
from rero_ils.modules.documents.utils import title_format_text_head
from rero_ils.modules.item_types.api import ItemTypesSearch
from rero_ils.modules.items.api import Item
from rero_ils.modules.items.models import ItemStatus
from rero_ils.modules.libraries.api import LibrariesSearch
from rero_ils.modules.locations.api import LocationsSearch
from rero_ils.modules.organisations.api import OrganisationsSearch
from rero_ils.modules.serializers import CachedDataSerializerMixin, \
    JSONSerializer
from rero_ils.modules.vendors.api import VendorsSearch


class ItemsJSONSerializer(JSONSerializer, CachedDataSerializerMixin):
    """Serializer for RERO-ILS `Item` records as JSON."""

    def _postprocess_search_hit(self, hit: dict) -> None:
        """Post-process each hit of a search result."""
        metadata = hit.get('metadata', {})
        doc_pid = metadata.get('document').get('pid')
        document = self.get_resource(DocumentsSearch(), doc_pid)
        metadata['ui_title_text'] = title_format_text_head(
            document['title'], with_subtitle=True)

        item = self.get_resource(Item, metadata.get('pid'))
        metadata['available'] = item.available
        metadata['availability'] = {
            'available': metadata['available'],
            'status': metadata['status'],
            'display_text': item.availability_text,
            'request': item.number_of_requests()
        }
        if not metadata['available'] \
           and metadata['status'] == ItemStatus.ON_LOAN:
            metadata['availability']['due_date'] = \
                item.get_item_end_date(format='long', language='en')

        # Item in collection
        if collection := item.in_collection():
            metadata['in_collection'] = collection
        # Temporary location
        if (temp_loc := metadata.get('temporary_location')) \
           and 'pid' in temp_loc:
            temp_loc_pid = temp_loc['pid']
            temp_loc['name'] = self\
                .get_resource(LocationsSearch(), temp_loc_pid).get('name')

        # Organisation
        org_pid = metadata['organisation']['pid']
        organisation = self.get_resource(OrganisationsSearch(), org_pid)
        metadata['organisation']['viewcode'] = organisation.get('code')
        # Library
        library_pid = metadata['library']['pid']
        library = self.get_resource(LibrariesSearch(), library_pid)
        metadata['library']['name'] = library.get('name')
        # Location
        location_pid = metadata['location']['pid']
        location = self.get_resource(LocationsSearch(), location_pid)
        metadata['location']['name'] = location.get('name')

        super()._postprocess_search_hit(hit)

    def _postprocess_search_aggregations(self, aggregations: dict) -> None:
        """Post-process aggregations from a search result."""
        JSONSerializer.enrich_bucket_with_data(
            aggregations.get('library', {}).get('buckets', []),
            LibrariesSearch, 'name'
        )
        JSONSerializer.enrich_bucket_with_data(
            aggregations.get('location', {}).get('buckets', []),
            LocationsSearch, 'name'
        )
        JSONSerializer.enrich_bucket_with_data(
            aggregations.get('item_type', {}).get('buckets', []),
            ItemTypesSearch, 'name'
        )
        JSONSerializer.enrich_bucket_with_data(
            aggregations.get('temporary_item_type', {}).get('buckets', []),
            ItemTypesSearch, 'name'
        )
        JSONSerializer.enrich_bucket_with_data(
            aggregations.get('temporary_location', {}).get('buckets', []),
            LocationsSearch, 'name'
        )
        JSONSerializer.enrich_bucket_with_data(
            aggregations.get('vendor', {}).get('buckets', []),
            VendorsSearch, 'name'
        )
        if aggregations.get('current_requests'):
            aggregations['current_requests']['type'] = 'range'
            aggregations['current_requests']['config'] = {
                'min': 1,
                'max': 100,
                'step': 1
            }
        super()._postprocess_search_aggregations(aggregations)
