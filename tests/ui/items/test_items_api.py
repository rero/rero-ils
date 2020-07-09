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

from datetime import datetime

import pytest
from utils import get_mapping

from rero_ils.modules.errors import RecordValidationError
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


def test_item_extended_validation(client, holding_lib_martigny_w_patterns):
    """Test item extended validation in relation with its parent holding."""
    data = {
        '$schema': 'https://ils.rero.ch/schemas/items/item-v0.0.1.json',
        'type': 'issue',
        'document': {
            '$ref': 'https://ils.rero.ch/api/documents/doc4'
        },
        'call_number': '00001',
        'location': {
            '$ref': 'https://ils.rero.ch/api/locations/loc1'
        },
        'item_type': {
            '$ref': 'https://ils.rero.ch/api/item_types/itty1'
        },
        'holding': {
            '$ref': 'https://ils.rero.ch/api/holdings/holding5'
        },
        'status': 'on_shelf'
    }
    data['issue'] = {
        'status': 'received',
        'display_text': 'irregular_issue',
        'received_date': datetime.now().strftime('%Y-%m-%d'),
        'expected_date': datetime.now().strftime('%Y-%m-%d'),
        'regular': False
    }
    Item.create(data, dbcommit=True, reindex=True, delete_pid=True)

    # can not have a standard item with issues on a serial holdings
    data['type'] = 'standard'
    with pytest.raises(RecordValidationError):
        Item.create(data, dbcommit=True, reindex=True, delete_pid=True)
    data['type'] == 'issue'
    data.pop('issue')
    # can not create an issue item without issues on a serial holdings
    with pytest.raises(RecordValidationError):
        Item.create(data, dbcommit=True, reindex=True, delete_pid=True)
