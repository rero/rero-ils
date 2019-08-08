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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

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
