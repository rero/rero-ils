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

"""Items Record tests."""

from __future__ import absolute_import, print_function

from utils import get_mapping

from rero_ils.modules.items.api import Item, ItemsSearch, item_id_fetcher
from rero_ils.modules.items.utils import item_location_retriever, \
    item_pid_to_object


def test_item_es_mapping(document, loc_public_martigny,
                         item_type_standard_martigny,
                         item_lib_martigny_data_tmp):
    """Test item elasticsearch mapping."""
    search = ItemsSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping
    Item.create(
        item_lib_martigny_data_tmp,
        dbcommit=True,
        reindex=True,
        delete_pid=True
    )
    assert mapping == get_mapping(search.Meta.index)


def test_item_organisation_pid(client, org_martigny, item_lib_martigny):
    """Test organisation pid has been added during the indexing."""
    search = ItemsSearch()
    item = next(search.filter('term', pid=item_lib_martigny.pid).scan())
    assert item.organisation.pid == org_martigny.pid


def test_item_item_location_retriever(item_lib_martigny, loc_public_martigny,
                                      loc_restricted_martigny):
    """Test location retriever for invenio-circulation."""
    assert item_location_retriever(item_pid_to_object(
        item_lib_martigny.pid)) == loc_public_martigny.pid


def test_item_get_items_pid_by_document_pid(document, item_lib_martigny):
    """Test get items by document pid."""
    assert len(list(Item.get_items_pid_by_document_pid(document.pid))) == 2


def test_item_create(item_lib_martigny_data_tmp, item_lib_martigny):
    """Test itemanisation creation."""
    item = Item.create(item_lib_martigny_data_tmp, delete_pid=True)
    assert item == item_lib_martigny_data_tmp
    # we have used item_lib_martigny_data_tmp two times -> pid == 2
    assert item.get('pid') == '2'
    assert item.can_delete

    item = Item.get_record_by_pid('1')
    item_lib_martigny_data_tmp['pid'] = '1'
    assert item == item_lib_martigny_data_tmp

    fetched_pid = item_id_fetcher(item.id, item)
    assert fetched_pid.pid_value == '1'
    assert fetched_pid.pid_type == 'item'

    item_lib_martigny.delete_from_index()
    assert not item_lib_martigny.delete_from_index()
    item_lib_martigny.dbcommit(forceindex=True)


def test_item_can_delete(item_lib_martigny):
    """Test can delete"""
    assert item_lib_martigny.get_links_to_me() == {}
    assert item_lib_martigny.can_delete
