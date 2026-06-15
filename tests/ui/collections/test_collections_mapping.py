# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Collections record mapping tests."""

from rero_ils.modules.collections.api import Collection, CollectionsSearch
from tests.utils import get_mapping


def test_collections_search_mapping(
    search,
    db,
    org_martigny,
    coll_martigny_1_data,
    item_lib_martigny,
    item2_lib_martigny,
):
    """Test collections search index mapping."""
    search = CollectionsSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping
    collection = Collection.create(coll_martigny_1_data, dbcommit=True, reindex=True, delete_pid=True)
    assert mapping == get_mapping(search.Meta.index)
    collection.delete(force=True, dbcommit=True, delindex=True)
