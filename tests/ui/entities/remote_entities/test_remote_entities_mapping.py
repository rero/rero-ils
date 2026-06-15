# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Mef entities record tests."""

from rero_ils.modules.entities.remote_entities.api import (
    RemoteEntitiesSearch,
    RemoteEntity,
)
from tests.utils import get_mapping


def test_remote_entity_search_mapping(search_clear, db, entity_person_data_tmp):
    """Test contribution entity search index mapping."""
    search = RemoteEntitiesSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping
    RemoteEntity.create(entity_person_data_tmp, dbcommit=True, reindex=True, delete_pid=True)
    assert mapping == get_mapping(search.Meta.index)


def test_concept_entity_search_mapping(search_clear, db, mef_concept1_data_tmp):
    """Test concept entity search index mapping."""
    search = RemoteEntitiesSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping
    RemoteEntity.create(mef_concept1_data_tmp, dbcommit=True, reindex=True, delete_pid=True)
    assert mapping == get_mapping(search.Meta.index)


def test_entities_search_mapping(app, entity_person):
    """Test Mef entities search mapping."""
    assert RemoteEntitiesSearch().query("query_string", query="philosophische Fakultät").count() == 1
    assert RemoteEntitiesSearch().query("match", **{"gnd.preferred_name": "Loy"}).count() == 1
    assert RemoteEntitiesSearch().query("match", **{"gnd.variant_name": "Madeiros"}).count() == 1
