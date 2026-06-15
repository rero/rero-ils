# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Signals connector for ItemTypes."""

from elasticsearch_dsl import Q

from rero_ils.modules.item_types.api import ItemType, ItemTypesIndexer
from rero_ils.modules.items.api import ItemsSearch

from ..tasks import process_bulk_queue


def negative_availability_changes(sender, record=None, *args, **kwargs):
    """Reindex related items if negative availability changes."""
    if not isinstance(record, ItemType):
        return
    ori_record = ItemType.get_record_by_pid(record.pid)
    record_availability = record.get("negative_availability", False)
    original_availability = ori_record.get("negative_availability", False)
    if record_availability != original_availability:
        search = (
            ItemsSearch()
            .filter(
                "bool",
                should=[
                    Q("match", item_type__pid=record.pid),
                    Q("match", temporary_item_type__pid=record.pid),
                ],
            )
            .source()
            .scan()
        )
        item_uuids = [hit.meta.id for hit in search]
        ItemTypesIndexer().bulk_index(item_uuids)
        process_bulk_queue.apply_async()
