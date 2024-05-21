# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2024 RERO+
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


"""Issues reindexing tests."""

from __future__ import absolute_import, print_function

from utils import flush_index

from rero_ils.modules.holdings.models import HoldingTypes
from rero_ils.modules.items.api import Item, ItemsSearch
from rero_ils.modules.items.models import ItemIssueStatus
from rero_ils.modules.tasks import process_bulk_queue
from rero_ils.modules.utils import get_ref_for_pid


def test_issue_location_after_holdings_update(
        holding_lib_martigny_w_patterns, loc_restricted_martigny,
        holding_lib_martigny_w_patterns_data):
    """Test location after holdings of type serials changes."""
    initial_holding_data = holding_lib_martigny_w_patterns_data
    holding = holding_lib_martigny_w_patterns
    assert holding.get('holdings_type') == HoldingTypes.SERIAL

    # create an item of type issue for this holdings
    item = holding.create_regular_issue(
        status=ItemIssueStatus.RECEIVED,
        dbcommit=True,
        reindex=True
    )
    assert ItemsSearch() \
        .filter('term', holding__pid=holding.pid) \
        .count() == 1
    assert item.location_pid == holding.location_pid

    # change the holdings location
    assert holding.location_pid != loc_restricted_martigny.pid
    holding['location'] = {'$ref': get_ref_for_pid(
        'locations', loc_restricted_martigny.pid)}
    holding = holding.update(holding, dbcommit=True, reindex=True)
    assert holding.location_pid == loc_restricted_martigny.pid

    # process the bulked indexed items
    process_bulk_queue()
    flush_index(ItemsSearch.Meta.index)

    # ensure that the location was correctly inherited from the holdings
    item = Item.get_record(item.id)
    assert item.location_pid == holding.location_pid
    assert ItemsSearch() \
        .filter('term', location__pid=holding.location_pid) \
        .count() == 1

    # clean up data
    holding.update(initial_holding_data, dbcommit=True, reindex=True)
    item.delete(force=True, dbcommit=True, delindex=True)
    assert ItemsSearch() \
        .filter('term', holding__pid=holding.pid) \
        .count() == 0


def test_issue_item_types_after_holdings_update(
        holding_lib_martigny_w_patterns, item_type_on_site_martigny,
        holding_lib_martigny_w_patterns_data):
    """Test item type after holdings of type serials changes."""
    initial_holding_data = holding_lib_martigny_w_patterns_data
    holding = holding_lib_martigny_w_patterns
    assert holding.get('holdings_type') == HoldingTypes.SERIAL

    # create an item of type issue for this holdings
    item = holding.create_regular_issue(
        status=ItemIssueStatus.RECEIVED,
        dbcommit=True,
        reindex=True
    )
    assert ItemsSearch() \
        .filter('term', holding__pid=holding.pid) \
        .count() == 1

    # change the holdings item_type
    assert holding.circulation_category_pid != item_type_on_site_martigny.pid
    holding['circulation_category'] = {'$ref': get_ref_for_pid(
        'item_types', item_type_on_site_martigny.pid)}
    holding = holding.update(holding, dbcommit=True, reindex=True)
    assert holding.circulation_category_pid == item_type_on_site_martigny.pid

    # process the bulked indexed items
    process_bulk_queue()
    flush_index(ItemsSearch.Meta.index)

    # ensure that the item type was correctly inherited from the holdings
    item = Item.get_record(item.id)
    assert item.item_type_pid == holding.circulation_category_pid
    assert ItemsSearch() \
        .filter('term', item_type__pid=holding.circulation_category_pid) \
        .count() == 1

    # clean up data
    holding.update(initial_holding_data, dbcommit=True, reindex=True)
    item.delete(force=True, dbcommit=True, delindex=True)
    ItemsSearch.flush_and_refresh()
    assert ItemsSearch() \
        .filter('term', holding__pid=holding.pid) \
        .count() == 0


def test_inherited_call_numbers_after_holdings_update(
        holding_lib_martigny_w_patterns, holding_lib_martigny_w_patterns_data):
    """Test call numbers after holdings of type serials changes."""
    initial_holding_data = holding_lib_martigny_w_patterns_data
    holding = holding_lib_martigny_w_patterns
    assert holding.get('holdings_type') == HoldingTypes.SERIAL

    # create an item of type issue for this holdings
    item = holding.create_regular_issue(
        status=ItemIssueStatus.RECEIVED,
        dbcommit=True,
        reindex=True
    )
    assert ItemsSearch() \
        .filter('term', holding__pid=holding.pid) \
        .count() == 1

    # change the holdings first call_number
    holding['call_number'] = 'cote1'
    holding = holding.update(holding, dbcommit=True, reindex=True)

    # process the bulked indexed items
    process_bulk_queue()
    ItemsSearch.flush_and_refresh()

    # ensure that the call number was correctly inherited from the holdings
    item = Item.get_record(item.id)
    assert ItemsSearch() \
        .filter('term', issue__inherited_first_call_number__raw='cote1')\
        .count() == 1
    assert ItemsSearch() \
        .filter('term', call_numbers__raw='cote1')\
        .count() == 1

    # delete holdings first call number and change the second call_number
    holding.pop('call_number', None)
    holding['second_call_number'] = 'cote2'
    holding = holding.replace(holding, dbcommit=True, reindex=True)

    # process the bulked indexed items
    process_bulk_queue()
    ItemsSearch.flush_and_refresh()

    # ensure that the call numbers were correctly inherited from the holdings
    item = Item.get_record(item.id)
    assert ItemsSearch() \
        .filter('term', issue__inherited_second_call_number__raw='cote2')\
        .count() == 1
    assert ItemsSearch() \
        .filter('term', call_numbers__raw='cote2')\
        .count() == 1
    assert ItemsSearch() \
        .filter('term', issue__inherited_first_call_number__raw='cote1')\
        .count() == 0
    assert ItemsSearch() \
        .filter('term', call_numbers__raw='cote1')\
        .count() == 0

    # clean up data
    holding.update(initial_holding_data, dbcommit=True, reindex=True)
    item.delete(force=True, dbcommit=True, delindex=True)
    assert ItemsSearch() \
        .filter('term', holding__pid=holding.pid) \
        .count() == 0
