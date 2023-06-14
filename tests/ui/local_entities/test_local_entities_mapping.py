# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
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

"""Item record mapping tests."""
from utils import get_mapping

from rero_ils.modules.entities.local_entities.api import LocalEntitiesSearch, \
    LocalEntity


def test_local_entities_es_mapping(app, local_entity_person2_data):
    """Test local entity elasticsearch mapping."""
    search = LocalEntitiesSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping
    LocalEntity.create(
        local_entity_person2_data,
        dbcommit=True,
        reindex=True,
        delete_pid=True
    )
    assert mapping == get_mapping(search.Meta.index)
