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


"""Holding Record tests."""


from __future__ import absolute_import, print_function

from copy import deepcopy

import pytest
from utils import flush_index

from rero_ils.modules.holdings.api import Holding, HoldingsSearch, \
    get_holdings_by_document_item_type
from rero_ils.modules.holdings.views import holding_loan_condition_filter
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
    assert item.holding_circulation_category_pid == \
        item_type_standard_martigny.pid

    item2 = deepcopy(item_lib_saxon_data)
    del item2['pid']
    item2 = Item.create(item2, dbcommit=True, reindex=True)
    flush_index(HoldingsSearch.Meta.index)
    assert item2.holding_pid != holding_lib_martigny.pid

    holding = Holding.get_record_by_pid(item2.holding_pid)
    assert holding.document_pid == document.pid
    assert holding.circulation_category_pid == item_type_standard_martigny.pid

    assert Holding.get_document_pid_by_holding_pid(item2.holding_pid) == \
        document.pid

    holdings = list(Holding.get_holdings_pid_by_document_pid(document.pid))
    assert holding_lib_martigny.pid in holdings
    assert item2.holding_pid in holdings

    can, reasons = holding_lib_martigny.can_delete
    assert not can
    assert reasons['links']['items']
    # test loan conditions
    assert holding_loan_condition_filter(holding_lib_martigny.pid) == \
        'standard'
    with pytest.raises(Exception):
        assert holding_loan_condition_filter('no pid')
    holdings = get_holdings_by_document_item_type(
        document.pid, item_type_standard_martigny.pid)
    assert holding_lib_martigny.pid == holdings[1].get('pid')
    assert list(holding_lib_martigny.get_items())[1].get('pid') == \
        item_lib_martigny.pid

    holding_lib_martigny.delete_from_index()
    assert not holding_lib_martigny.delete_from_index()
    holding_lib_martigny.dbcommit(forceindex=True)

    # test item count by holdings pid
    assert holding_lib_martigny.get_items_count_by_holding_pid == 2


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

    can, reasons = holding.can_delete
    assert not can
    assert reasons['links']['items']

    item_lib_martigny.delete(dbcommit=True, delindex=True)
    flush_index(ItemsSearch.Meta.index)

    pid = holding_lib_martigny.pid
    holding = Holding.get_record_by_pid(pid)
    assert not holding


def test_holding_delete_after_item_edition(
        client, holding_lib_saxon, item_lib_saxon, holding_lib_fully):
    """Test automatic holding delete after item edition."""

    item_lib_saxon['location'] = \
        {'$ref': 'https://bib.rero.ch/api/locations/loc5'}

    item_lib_saxon.update(item_lib_saxon, dbcommit=True, reindex=True)
    flush_index(ItemsSearch.Meta.index)
    item = Item.get_record_by_pid(item_lib_saxon.pid)
    assert item.holding_pid == holding_lib_fully.pid

    holding = Holding.get_record_by_pid(holding_lib_saxon.pid)
    assert holding.get_links_to_me() == {}
