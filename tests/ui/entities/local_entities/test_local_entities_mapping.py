# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Item record mapping tests."""

from rero_ils.modules.entities.local_entities.api import (
    LocalEntitiesSearch,
    LocalEntity,
)
from tests.utils import get_mapping


def test_local_entities_search_mapping(app, local_entity_person2_data):
    """Test local entity search index mapping."""
    search = LocalEntitiesSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping
    LocalEntity.create(local_entity_person2_data, dbcommit=True, reindex=True, delete_pid=True)
    assert mapping == get_mapping(search.Meta.index)
