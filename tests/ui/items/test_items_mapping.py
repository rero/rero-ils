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
from rero_ils.modules.items.api import Item, ItemsSearch
from tests.utils import get_mapping


def test_item_es_mapping(
    document,
    loc_public_martigny,
    item_type_standard_martigny,
    item_lib_martigny_data_tmp,
):
    """Test item elasticsearch mapping."""
    search = ItemsSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping
    Item.create(
        item_lib_martigny_data_tmp, dbcommit=True, reindex=True, delete_pid=True
    )
    assert mapping == get_mapping(search.Meta.index)
