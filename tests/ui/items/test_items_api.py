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

"""CircPolicy Record tests."""

from __future__ import absolute_import, print_function

from utils import get_mapping

from rero_ils.modules.items.api import Item, ItemsSearch, item_id_fetcher


def test_item_create(db, es_clear, item_on_loan_data_tmp):
    """Test itemanisation creation."""
    item = Item.create(item_on_loan_data_tmp)
    assert item == item_on_loan_data_tmp
    assert item.get('pid') == '1'

    item = Item.get_record_by_pid('1')
    assert item == item_on_loan_data_tmp

    fetched_pid = item_id_fetcher(item.id, item)
    assert fetched_pid.pid_value == '1'
    assert fetched_pid.pid_type == 'item'


def test_item_es_mapping(es_clear, db, document, location, item_type,
                         item_on_loan_data_tmp):
    """."""
    search = ItemsSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping
    Item.create(item_on_loan_data_tmp, dbcommit=True, reindex=True)
    assert mapping == get_mapping(search.Meta.index)


def test_item_get_items_pid_by_document_pid(document, item_on_shelf):
    """."""
    assert len(list(Item.get_items_pid_by_document_pid(document.pid))) == 1
