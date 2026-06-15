# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Item type search index mapping tests."""

from rero_ils.modules.item_types.api import ItemType, ItemTypesSearch
from tests.utils import get_mapping


def test_item_type_search_mapping(search, db, org_martigny, item_type_data_tmp):
    """Test item type search index mapping."""
    search = ItemTypesSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping
    itty = ItemType.create(item_type_data_tmp, dbcommit=True, reindex=True, delete_pid=True)
    assert mapping == get_mapping(search.Meta.index)
    itty.delete(force=True, dbcommit=True, delindex=True)


def test_item_types_search_mapping(app, item_types_records):
    """Test item type search mapping."""
    search = ItemTypesSearch()

    assert search.query("query_string", query="checkout").count() == 2
    assert search.query("match", name="checkout").count() == 0

    eq_query = search.query("match", name="specific").source(["pid"]).scan()
    pids = [hit.pid for hit in eq_query]
    assert len(pids) == 1
    assert "itty3" in pids
