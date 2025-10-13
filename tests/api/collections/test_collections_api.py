# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2020 RERO
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

"""Test item collections."""

import pytest
from jsonschema.exceptions import ValidationError


def test_get_items(item_lib_martigny, item2_lib_martigny, coll_martigny_1):
    """Test get items for a collection"""
    # collection should have 2 items
    assert coll_martigny_1.get_items() == [item_lib_martigny, item2_lib_martigny]

    item_lib_martigny.delete(dbcommit=True, delindex=True)
    # after deleting on item collection should have only one item
    assert coll_martigny_1.get_items() == [item2_lib_martigny]


def test_get_libraries(coll_martigny_1, lib_martigny):
    """Test get library pids for a collection."""
    assert coll_martigny_1.library_pids[0] == lib_martigny["pid"]


def test_collections_extended_validation(lib_fully, item_lib_fully, coll_martigny_1):
    """Test that all items in the collection belong to a selected library."""
    # check that there is no validation error with items from martigny library
    assert coll_martigny_1.update(coll_martigny_1)

    coll_martigny_1["items"].append({"$ref": "https://bib.rero.ch/api/items/item3"})
    with pytest.raises(ValidationError) as err:
        coll_martigny_1.update(coll_martigny_1, dbcommit=True, reindex=True)
    assert "items should belong to one of the selected libraries" in str(err)

    # add fully library to the collection
    coll_martigny_1["libraries"].append({"$ref": "https://bib.rero.ch/api/libraries/lib3"})

    # check that now the collection can be saved
    assert coll_martigny_1.update(coll_martigny_1)
