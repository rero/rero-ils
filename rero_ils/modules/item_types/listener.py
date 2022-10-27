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

"""Signals connector for ItemTypes."""
from elasticsearch_dsl import Q

from rero_ils.modules.item_types.api import ItemType, ItemTypesIndexer
from rero_ils.modules.items.api import ItemsSearch

from ..tasks import process_bulk_queue


def negative_availability_changes(sender, record=None, *args, **kwargs):
    """Reindex related items if negative availability changes."""
    if isinstance(record, ItemType):
        ori_record = ItemType.get_record_by_pid(record.pid)
        record_availability = record.get('negative_availability', False)
        original_availability = ori_record.get('negative_availability', False)
        if record_availability != original_availability:
            # get all item uuid's related to the item type and mark them for
            # reindex into a asynchronous celery queue.
            item_uuids = []
            search = ItemsSearch()\
                .filter('bool', should=[
                    Q('match', item_type__pid=record.pid),
                    Q('match', temporary_item_type__pid=record.pid)
                ]) \
                .source().scan()
            for hit in search:
                item_uuids.append(hit.meta.id)
            ItemTypesIndexer().bulk_index(item_uuids)
            process_bulk_queue.apply_async()
