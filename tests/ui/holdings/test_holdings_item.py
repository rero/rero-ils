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

"""Holding Record tests."""

from __future__ import absolute_import, print_function

from copy import deepcopy

from utils import flush_index

from rero_ils.modules.holdings.api import Holding, HoldingsSearch
from rero_ils.modules.items.api import Item, ItemsSearch


def test_holding_item_links(client, holding_lib_martigny, item_lib_martigny,
                            item_lib_martigny_data, document,
                            item_type_on_site_martigny, loc_public_martigny,
                            item_lib_saxon_data, loc_public_saxon,
                            item_type_standard_martigny):
    """Test holding and item links."""
    item = deepcopy(item_lib_martigny_data)
    del item['pid']
    item['barcode'] = 'barcode'
    item = Item.create(item, dbcommit=True, reindex=True)
    flush_index(HoldingsSearch.Meta.index)
    assert item.holding_pid == holding_lib_martigny.pid

    item2 = deepcopy(item_lib_saxon_data)
    del item2['pid']
    item2 = Item.create(item2, dbcommit=True, reindex=True)
    flush_index(HoldingsSearch.Meta.index)
    assert item2.holding_pid != holding_lib_martigny.pid

    holding = Holding.get_record_by_pid(item2.holding_pid)
    assert holding.document_pid == document.pid
    assert holding.circulation_type_pid == item_type_standard_martigny.pid

    assert Holding.get_document_pid_by_holding_pid(item2.holding_pid) == \
        document.pid

    holdings = list(Holding.get_holdings_pid_by_document_pid(document.pid))
    assert holding_lib_martigny.pid in holdings
    assert item2.holding_pid in holdings

    assert holding_lib_martigny.get_links_to_me().get('items')
    assert not holding_lib_martigny.can_delete


def test_holding_delete_after_item_deletion(
        client, holding_lib_martigny, item_lib_martigny):
    """Test automatic holding delete after deleting last item."""
    for pid in Item.get_all_pids():
        if pid != item_lib_martigny.pid:
            item = Item.get_record_by_pid(pid)
            Item.delete(item, dbcommit=True, delindex=True)
            flush_index(ItemsSearch.Meta.index)

    pid = holding_lib_martigny.pid
    holding = Holding.get_record_by_pid(pid)
    assert not holding.can_delete

    item_lib_martigny.delete(dbcommit=True, delindex=True)
    flush_index(ItemsSearch.Meta.index)

    pid = holding_lib_martigny.pid
    holding = Holding.get_record_by_pid(pid)
    assert not holding
