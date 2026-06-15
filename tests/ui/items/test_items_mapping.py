# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Item record mapping tests."""

from rero_ils.modules.items.api import Item, ItemsSearch
from tests.utils import get_mapping


def test_item_search_mapping(
    document,
    loc_public_martigny,
    item_type_standard_martigny,
    item_lib_martigny_data_tmp,
):
    """Test item search index mapping."""
    search = ItemsSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping
    Item.create(item_lib_martigny_data_tmp, dbcommit=True, reindex=True, delete_pid=True)
    assert mapping == get_mapping(search.Meta.index)


def test_item_sort_call_number(
    document,
    loc_public_martigny,
    item_type_standard_martigny,
    item_lib_martigny_data_tmp,
):
    """Test sort_call_number is correctly populated in the search index.

    For a regular item, sort_call_number must equal the item's own call_number.
    For a regular item with no call_number, sort_call_number must be absent/None.
    """
    # CHECK_1 :: item has call_number → sort_call_number matches it
    item_lib_martigny_data_tmp["call_number"] = "SORT-CN-TEST"
    item_lib_martigny_data_tmp.pop("second_call_number", None)
    item = Item.create(item_lib_martigny_data_tmp, dbcommit=True, reindex=True, delete_pid=True)
    ItemsSearch.flush_and_refresh()

    hit = ItemsSearch().filter("term", pid=item.pid).source(True).execute().hits[0]
    assert hit.sort_call_number == "SORT-CN-TEST"
    assert "sort_second_call_number" not in hit.to_dict()

    # CHECK_2 :: item also has second_call_number → sort_second_call_number matches it
    item["second_call_number"] = "SORT-CN2-TEST"
    item.update(item, dbcommit=True, reindex=True)
    ItemsSearch.flush_and_refresh()

    hit = ItemsSearch().filter("term", pid=item.pid).source(True).execute().hits[0]
    assert hit.sort_second_call_number == "SORT-CN2-TEST"

    # CHECK_3 :: item has no call_number at all → sort_call_number must be absent
    item.pop("call_number", None)
    item.pop("second_call_number", None)
    item.update(item, dbcommit=True, reindex=True)
    ItemsSearch.flush_and_refresh()

    hit = ItemsSearch().filter("term", pid=item.pid).source(True).execute().hits[0]
    assert "sort_call_number" not in hit.to_dict()
    assert "sort_second_call_number" not in hit.to_dict()
