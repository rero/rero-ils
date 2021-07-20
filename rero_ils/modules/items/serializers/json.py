# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
# Copyright (C) 2020 UCLouvain
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

"""Item serializers."""

from rero_ils.modules.documents.api import search_document_by_pid
from rero_ils.modules.documents.utils import filter_document_type_buckets, \
    title_format_text_head
from rero_ils.modules.item_types.api import ItemType
from rero_ils.modules.items.api import Item
from rero_ils.modules.items.models import ItemStatus
from rero_ils.modules.libraries.api import Library
from rero_ils.modules.locations.api import Location
from rero_ils.modules.organisations.api import Organisation
from rero_ils.modules.serializers import JSONSerializer
from rero_ils.modules.vendors.api import Vendor


class ItemsJSONSerializer(JSONSerializer):
    """Mixin serializing records as JSON."""

    def post_process_serialize_search(self, results, pid_fetcher):
        """Post process the search results.

        :param results: Elasticsearch search result.
        :param pid_fetcher: Persistent identifier fetcher.
        """
        records = results.get('hits', {}).get('hits', {})
        orgs = {}
        libs = {}
        locs = {}
        for record in records:
            metadata = record.get('metadata', {})
            document = search_document_by_pid(
                metadata.get('document').get('pid')
            )
            metadata['ui_title_text'] = title_format_text_head(
                document['title'],
                with_subtitle=True
            )

            item = Item.get_record_by_pid(metadata.get('pid'))
            metadata['available'] = item.available
            metadata['availability'] = {
                'available': metadata['available'],
                'status': metadata['status'],
                'display_text': item.availability_text,
                'request': item.number_of_requests()
            }
            if not metadata['available']:
                if metadata['status'] == ItemStatus.ON_LOAN:
                    metadata['availability']['due_date'] =\
                        item.get_item_end_date(format='long', language='en')

            # Item in collection
            collection = item.in_collection()
            if collection:
                metadata['in_collection'] = collection

            # Temporary location
            temp_location = metadata.get('temporary_location')
            if temp_location:
                temp_location_pid = temp_location['pid']
                if temp_location_pid not in locs:
                    locs[temp_location_pid] = Location \
                        .get_record_by_pid(temp_location_pid)
                temp_location['name'] = locs[temp_location_pid].get('name')

            # Organisation
            organisation = metadata['organisation']
            if organisation['pid'] not in orgs:
                orgs[organisation['pid']] = Organisation \
                    .get_record_by_pid(organisation['pid'])
            organisation['viewcode'] = orgs[organisation['pid']].get('code')
            # Library
            library = metadata['library']
            if library['pid'] not in libs:
                libs[library['pid']] = Library \
                    .get_record_by_pid(library['pid'])
            library['name'] = libs[library['pid']].get('name')
            # Location
            location = metadata['location']
            if location['pid'] not in locs:
                locs[location['pid']] = Location \
                    .get_record_by_pid(location['pid'])
            location['name'] = locs[location['pid']].get('name')

        # Add library name
        for lib_term in results.get('aggregations', {}).get(
                'library', {}).get('buckets', []):
            lib = Library.get_record_by_pid(lib_term.get('key'))
            lib_term['name'] = lib.get('name')
        # Add location name
        for loc_term in results.get('aggregations', {}).get(
                'location', {}).get('buckets', []):
            loc = Location.get_record_by_pid(loc_term.get('key'))
            loc_term['name'] = loc.get('name')

        # Add item type name
        for item_type_term in results.get('aggregations', {}).get(
                'item_type', {}).get('buckets', []):
            item_type = ItemType.get_record_by_pid(item_type_term.get('key'))
            item_type_term['name'] = item_type.get('name')

        # Add vendor name
        for vendor_term in results.get('aggregations', {}).get(
                'vendor', {}).get('buckets', []):
            vendor = Vendor.get_record_by_pid(vendor_term.get('key'))
            vendor_term['name'] = vendor.get('name')

        # Correct document type buckets
        if results.get('aggregations', {}).get('document_type'):
            buckets = results['aggregations']['document_type']['buckets']
            results['aggregations']['document_type']['buckets'] = \
                filter_document_type_buckets(buckets)

        return super().post_process_serialize_search(results, pid_fetcher)
