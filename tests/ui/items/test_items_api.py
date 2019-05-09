# -*- coding: utf-8 -*-
#
# This file is part of RERO ILS.
# Copyright (C) 2017 RERO.
#
# RERO ILS is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# RERO ILS is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RERO ILS; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Items Record tests."""

from __future__ import absolute_import, print_function

from utils import get_mapping

from rero_ils.modules.items.api import Item, ItemsSearch, item_id_fetcher


def test_item_item_location_retriever(item_lib_martigny, loc_public_martigny,
                                      loc_restricted_martigny):
    """Test location retriever for invenio-circulation."""
    assert item_lib_martigny.item_location_retriever(
        item_lib_martigny.pid) == loc_public_martigny.pid


def test_item_get_items_pid_by_document_pid(document, item_lib_martigny):
    """Test get items by document pid."""
    assert len(list(Item.get_items_pid_by_document_pid(document.pid))) == 1


def test_item_create(db, es_clear, item_lib_martigny_data_tmp):
    """Test itemanisation creation."""
    item = Item.create(item_lib_martigny_data_tmp, delete_pid=True)
    assert item == item_lib_martigny_data_tmp
    assert item.get('pid') == '1'
    assert item.can_delete

    item = Item.get_record_by_pid('1')
    assert item == item_lib_martigny_data_tmp

    fetched_pid = item_id_fetcher(item.id, item)
    assert fetched_pid.pid_value == '1'
    assert fetched_pid.pid_type == 'item'


def test_item_organisation_pid(org_martigny, item_lib_martigny):
    """Test organisation pid has been added during the indexing."""
    search = ItemsSearch()
    item = next(search.filter('term', pid=item_lib_martigny.pid).scan())
    assert item.organisation.pid == org_martigny.pid


def test_item_item_location_retriever(item_lib_martigny, loc_public_martigny,
                                      loc_restricted_martigny):
    """Test location retriever for invenio-circulation."""
    assert item_lib_martigny.item_location_retriever(
        item_lib_martigny.pid) == loc_public_martigny.pid


def test_item_get_items_pid_by_document_pid(document, item_lib_martigny):
    """."""
    assert len(list(Item.get_items_pid_by_document_pid(document.pid))) == 1


def test_item_can_delete(item_lib_martigny):
    """Test can delete"""
    assert item_lib_martigny.get_links_to_me() == {}
    assert item_lib_martigny.can_delete


def test_item_es_mapping(es_clear, db, document, loc_public_martigny,
                         item_type_standard_martigny,
                         item_lib_martigny_data_tmp):
    """."""
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


def test_item_can_delete(item_lib_martigny):
    """Test can delete."""
    assert item_lib_martigny.get_links_to_me() == {}
    assert item_lib_martigny.can_delete
