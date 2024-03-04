# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2024 RERO
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

"""API for manipulating collections."""

from datetime import datetime, timezone
from functools import partial

from rero_ils.modules.items.api import Item

from .models import CollectionIdentifier, CollectionMetadata
from ..api import IlsRecord, IlsRecordsIndexer, IlsRecordsSearch
from ..fetchers import id_fetcher
from ..minters import id_minter
from ..providers import Provider
from ..utils import extracted_data_from_ref

# provider
CollectionProvider = type(
    'CollectionProvider',
    (Provider,),
    dict(identifier=CollectionIdentifier, pid_type='coll')
)
# minter
collection_id_minter = partial(id_minter, provider=CollectionProvider)
# fetcher
collection_id_fetcher = partial(id_fetcher, provider=CollectionProvider)


class CollectionsSearch(IlsRecordsSearch):
    """CollectionsSearch."""

    class Meta:
        """Search only on collection index."""

        index = 'collections'
        doc_types = None

    def active_by_item_pid(self, item_pid):
        """Search for active collections by item pid.

        :param item_pid: string - the item to filter with.
        :return: An ElasticSearch query to get hits related the entity.
        """
        return self \
            .filter('term', items__pid=item_pid) \
            .filter('range', end_date={'gte': datetime.now(timezone.utc)}) \
            .sort({'end_date': {'order': 'asc'}})


class Collection(IlsRecord):
    """Collection class."""

    minter = collection_id_minter
    fetcher = collection_id_fetcher
    provider = CollectionProvider
    model_cls = CollectionMetadata
    pids_exist_check = {
        'not_required': {
            'doc': 'document',
            'lib': 'library',
            'loc': 'location',
            'item': 'item'
        }
    }

    def get_items(self):
        """Get items.

        :param self: self
        :return: list of items linked to collection
        """
        items = []
        for item in self.get('items', []):
            item_pid = extracted_data_from_ref(item)
            item = Item.get_record_by_pid(item_pid)
            # inherit holdings first call number when possible
            if first_call_number := item.issue_inherited_first_call_number:
                item['call_number'] = first_call_number
            # inherit holdings second call number when possible
            if second_call_number := item.issue_inherited_second_call_number:
                item['second_call_number'] = second_call_number

            items.append(item)
        return items


class CollectionsIndexer(IlsRecordsIndexer):
    """Indexing collections in Elasticsearch."""

    record_cls = Collection

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(record_id_iterator, doc_type='coll')
