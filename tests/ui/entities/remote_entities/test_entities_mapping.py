# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
# Copyright (C) 2019-2023 UCLouvain
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

"""Mef entities record tests."""

from utils import get_mapping

from rero_ils.modules.entities.remote_entities.api import \
    RemoteEntitiesSearch, RemoteEntity


def test_remote_entity_es_mapping(es_clear, db, entity_person_data_tmp):
    """Test contribution entity elasticsearch mapping."""
    search = RemoteEntitiesSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping
    RemoteEntity.create(
        entity_person_data_tmp,
        dbcommit=True,
        reindex=True,
        delete_pid=True
    )
    assert mapping == get_mapping(search.Meta.index)


def test_concept_entity_es_mapping(es_clear, db, mef_concept1_data_tmp):
    """Test concept entity elasticsearch mapping."""
    search = RemoteEntitiesSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping
    RemoteEntity.create(
        mef_concept1_data_tmp,
        dbcommit=True,
        reindex=True,
        delete_pid=True
    )
    assert mapping == get_mapping(search.Meta.index)


def test_entities_search_mapping(app, entity_person):
    """Test Mef entities search mapping."""
    assert RemoteEntitiesSearch()\
        .query('query_string', query='philosophische Fakultät')\
        .count() == 1
    assert RemoteEntitiesSearch()\
        .query('match', **{'gnd.preferred_name': 'Loy'})\
        .count() == 1
    assert RemoteEntitiesSearch()\
        .query('match', **{'gnd.variant_name': 'Madeiros'})\
        .count() == 1
