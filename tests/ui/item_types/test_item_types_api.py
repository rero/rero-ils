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

"""Item type record tests."""

from __future__ import absolute_import, print_function

from utils import get_mapping

from rero_ils.modules.item_types.api import ItemType, ItemTypesSearch, \
    item_type_id_fetcher


def test_item_type_create(db, item_type_data_tmp):
    """Test item type record creation."""
    itty = ItemType.create(item_type_data_tmp, delete_pid=True)
    assert itty == item_type_data_tmp
    assert itty.get('pid') == '1'

    itty = ItemType.get_record_by_pid('1')
    assert itty == item_type_data_tmp

    fetched_pid = item_type_id_fetcher(itty.id, itty)
    assert fetched_pid.pid_value == '1'
    assert fetched_pid.pid_type == 'itty'
    assert not ItemType.get_pid_by_name('no exists')


def test_item_type_es_mapping(es_clear, db, org_martigny, item_type_data_tmp):
    """Test item type elasticsearch mapping."""
    search = ItemTypesSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping
    ItemType.create(
        item_type_data_tmp,
        dbcommit=True,
        reindex=True,
        delete_pid=True
    )
    assert mapping == get_mapping(search.Meta.index)


def test_item_type_exist_name_and_organisation_pid(
        item_type_standard_martigny):
    """Test item type name uniquness."""
    item_type = item_type_standard_martigny
    itty = item_type.replace_refs()
    assert ItemType.exist_name_and_organisation_pid(
        itty.get('name'), itty.get('organisation', {}).get('pid'))
    assert not ItemType.exist_name_and_organisation_pid(
        'not exists yet', itty.get('organisation', {}).get('pid'))


def test_item_type_get_pid_by_name(item_type_standard_martigny):
    """Test item type retrival by name."""
    assert not ItemType.get_pid_by_name('no exists')
    assert ItemType.get_pid_by_name('standard') == 'itty1'


def test_item_type_can_not_delete(item_type_standard_martigny,
                                  item_lib_martigny):
    """Test item type can not delete"""
    links = item_type_standard_martigny.get_links_to_me()
    assert links['items'] == 1
    assert not item_type_standard_martigny.can_delete


def test_item_type_can_delete(app, item_type_data_tmp):
    """Test item type can delete"""
    itty = ItemType.create(item_type_data_tmp, delete_pid=True)
    assert itty.get_links_to_me() == {}
    assert itty.can_delete
