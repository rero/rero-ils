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
from rero_ils.modules.documents.extensions import TitleExtension
from rero_ils.modules.item_types.api import ItemTypesSearch
from rero_ils.modules.items.api import Item
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
        def _set_item_type_circulation_information(metadata, pid):
            """Get Item type circulation information.

            :param: metadata: The item record.
            :param: pid: the item type pid.
            """
            record = self.get_resource(ItemTypesSearch(), pid) or {}
            if circulation := record.get('circulation_information'):
                metadata['item_type']['circulation_information'] = circulation

        metadata = hit.get('metadata', {})
        doc_pid = metadata.get('document').get('pid')
        document = self.get_resource(DocumentsSearch(), doc_pid)
        metadata['ui_title_text'] = TitleExtension.format_text(
            document['title'], with_subtitle=True)

        item = self.get_resource(Item, metadata.get('pid'))

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

        # Try to serialize circulation information from best possible
        # related `ItemType` resource if exists.
        if itty_pid := metadata.get('temporary_item_type', {}).get('pid'):
            itty_rec = self.get_resource(ItemTypesSearch(), itty_pid) or {}
            if circulation := itty_rec.get('circulation_information'):
                metadata['item_type']['circulation_information'] = circulation

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
        if aggr := aggregations.get('claims_date'):
            JSONSerializer.add_date_range_configuration(aggr)

        super()._postprocess_search_aggregations(aggregations)

    def preprocess_record(self, pid, record, links_factory=None, **kwargs):
        """Prepare a record and persistent identifier for serialization.

        :param pid: Persistent identifier instance.
        :param record: Record instance.
        :param links_factory: Factory function for record links.
        """
        if record.is_issue and (notifications := record.claim_notifications):
            dates = [
                notification['creation_date']
                for notification in notifications
                if 'creation_date' in notification
            ]
            record.setdefault('issue', {})['claims'] = {
                'counter': len(notifications),
                'dates': dates
            }
        return super().preprocess_record(
            pid=pid, record=record, links_factory=links_factory, kwargs=kwargs)
