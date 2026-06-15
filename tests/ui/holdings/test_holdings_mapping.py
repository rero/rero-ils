# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Holdingss record mapping tests."""

from rero_ils.modules.holdings.api import Holding, HoldingsSearch
from tests.utils import get_mapping


def test_holding_search_mapping(
    search,
    db,
    loc_public_martigny,
    item_type_standard_martigny,
    document,
    holding_lib_martigny_data,
):
    """Test holding search index mapping."""
    search = HoldingsSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping
    holding = Holding.create(holding_lib_martigny_data, dbcommit=True, reindex=True, delete_pid=True)
    assert mapping == get_mapping(search.Meta.index)
    # clean created data
    holding.delete(force=True, dbcommit=True, delindex=True)
