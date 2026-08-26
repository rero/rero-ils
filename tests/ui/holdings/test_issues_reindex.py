# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Issues reindexing tests."""

from unittest import mock

from rero_ils.modules.holdings.models import HoldingTypes
from rero_ils.modules.items.api import Item, ItemsIndexer, ItemsSearch
from rero_ils.modules.items.models import ItemIssueStatus
from rero_ils.modules.tasks import process_bulk_queue
from rero_ils.modules.utils import get_ref_for_pid


def test_issue_location_after_holdings_update(
    holding_lib_martigny_w_patterns,
    loc_restricted_martigny,
    holding_lib_martigny_w_patterns_data,
):
    """Test location after holdings of type serials changes."""
    initial_holding_data = holding_lib_martigny_w_patterns_data
    holding = holding_lib_martigny_w_patterns
    assert holding.get("holdings_type") == HoldingTypes.SERIAL

    # create an item of type issue for this holdings
    item = holding.create_regular_issue(status=ItemIssueStatus.RECEIVED, dbcommit=True, reindex=True)
    assert ItemsSearch().filter("term", holding__pid=holding.pid).count() == 1
    assert item.location_pid == holding.location_pid

    # change the holdings location
    assert holding.location_pid != loc_restricted_martigny.pid
    holding["location"] = {"$ref": get_ref_for_pid("locations", loc_restricted_martigny.pid)}
    holding = holding.update(holding, dbcommit=True, reindex=True)
    assert holding.location_pid == loc_restricted_martigny.pid

    # process the bulked indexed items
    process_bulk_queue()
    ItemsSearch.flush_and_refresh()

    # ensure that the location was correctly inherited from the holdings
    item = Item.get_record(item.id)
    assert item.location_pid == holding.location_pid
    assert ItemsSearch().filter("term", location__pid=holding.location_pid).count() == 1

    # clean up data ; restore the module scoped fixture record itself, as
    # `update(dbcommit=True)` returned another instance.
    holding_lib_martigny_w_patterns.update(initial_holding_data, dbcommit=True, reindex=True)
    item.delete(force=True, dbcommit=True, delindex=True)
    assert ItemsSearch().filter("term", holding__pid=holding.pid).count() == 0


def test_issue_not_indexed_when_inheritance_fails(
    holding_lib_martigny_w_patterns,
    loc_restricted_martigny,
    holding_lib_martigny_w_patterns_data,
    caplog,
):
    """Test a failed field inheritance is logged and the item is not indexed."""
    initial_holding_data = holding_lib_martigny_w_patterns_data
    holding = holding_lib_martigny_w_patterns

    item = holding.create_regular_issue(status=ItemIssueStatus.RECEIVED, dbcommit=True, reindex=True)
    initial_location_pid = item.location_pid

    # change the holdings location, but make the item update fail
    holding["location"] = {"$ref": get_ref_for_pid("locations", loc_restricted_martigny.pid)}
    with (
        mock.patch(
            "rero_ils.modules.holdings.listener.get_ref_for_pid",
            side_effect=Exception("inheritance failure"),
        ),
        mock.patch.object(ItemsIndexer, "bulk_index") as mock_bulk_index,
    ):
        holding.update(holding, dbcommit=True, reindex=True)

    # the failure is reported and the untouched item is not reindexed
    assert "Unable to inherit holding" in caplog.text
    mock_bulk_index.assert_not_called()
    assert Item.get_record(item.id).location_pid == initial_location_pid

    # clean up data
    holding.update(initial_holding_data, dbcommit=True, reindex=True)
    item.delete(force=True, dbcommit=True, delindex=True)


def test_issues_partially_inherit_when_one_fails(
    holding_lib_martigny_w_patterns,
    loc_restricted_martigny,
    holding_lib_martigny_w_patterns_data,
    caplog,
):
    """Test a failing item does not prevent the other ones from inheriting."""
    initial_holding_data = holding_lib_martigny_w_patterns_data
    holding = holding_lib_martigny_w_patterns

    items = [
        holding.create_regular_issue(status=ItemIssueStatus.RECEIVED, dbcommit=True, reindex=True) for _ in range(2)
    ]
    initial_location_pid = items[0].location_pid

    # change the holdings location, but make the first item update fail
    new_location_ref = get_ref_for_pid("locations", loc_restricted_martigny.pid)
    holding["location"] = {"$ref": new_location_ref}
    with (
        mock.patch(
            "rero_ils.modules.holdings.listener.get_ref_for_pid",
            side_effect=[Exception("inheritance failure"), new_location_ref],
        ),
        mock.patch.object(ItemsIndexer, "bulk_index") as mock_bulk_index,
    ):
        holding.update(holding, dbcommit=True, reindex=True)

    # the failed item keeps its location, the other one inherits the new one
    assert "Unable to inherit holding" in caplog.text
    assert sorted(Item.get_record(item.id).location_pid for item in items) == sorted(
        [initial_location_pid, loc_restricted_martigny.pid]
    )
    # and only the updated item is sent to the indexer
    mock_bulk_index.assert_called_once()
    assert len(mock_bulk_index.call_args[0][0]) == 1

    # clean up data
    holding.update(initial_holding_data, dbcommit=True, reindex=True)
    for item in items:
        item.delete(force=True, dbcommit=True, delindex=True)


def test_issue_item_types_after_holdings_update(
    holding_lib_martigny_w_patterns,
    item_type_on_site_martigny,
    holding_lib_martigny_w_patterns_data,
):
    """Test item type after holdings of type serials changes."""
    initial_holding_data = holding_lib_martigny_w_patterns_data
    holding = holding_lib_martigny_w_patterns
    assert holding.get("holdings_type") == HoldingTypes.SERIAL

    # create an item of type issue for this holdings
    item = holding.create_regular_issue(status=ItemIssueStatus.RECEIVED, dbcommit=True, reindex=True)
    assert ItemsSearch().filter("term", holding__pid=holding.pid).count() == 1

    # change the holdings item_type
    assert holding.circulation_category_pid != item_type_on_site_martigny.pid
    holding["circulation_category"] = {"$ref": get_ref_for_pid("item_types", item_type_on_site_martigny.pid)}
    holding = holding.update(holding, dbcommit=True, reindex=True)
    assert holding.circulation_category_pid == item_type_on_site_martigny.pid

    # process the bulked indexed items
    process_bulk_queue()
    ItemsSearch.flush_and_refresh()

    # ensure that the item type was correctly inherited from the holdings
    item = Item.get_record(item.id)
    assert item.item_type_pid == holding.circulation_category_pid
    assert ItemsSearch().filter("term", item_type__pid=holding.circulation_category_pid).count() == 1

    # clean up data ; restore the module scoped fixture record itself, as
    # `update(dbcommit=True)` returned another instance.
    holding_lib_martigny_w_patterns.update(initial_holding_data, dbcommit=True, reindex=True)
    item.delete(force=True, dbcommit=True, delindex=True)
    ItemsSearch.flush_and_refresh()
    assert ItemsSearch().filter("term", holding__pid=holding.pid).count() == 0


def test_inherited_call_numbers_after_holdings_update(
    holding_lib_martigny_w_patterns, holding_lib_martigny_w_patterns_data
):
    """Test call numbers after holdings of type serials changes."""
    initial_holding_data = holding_lib_martigny_w_patterns_data
    holding = holding_lib_martigny_w_patterns
    assert holding.get("holdings_type") == HoldingTypes.SERIAL

    # create an item of type issue for this holdings
    item = holding.create_regular_issue(status=ItemIssueStatus.RECEIVED, dbcommit=True, reindex=True)
    assert ItemsSearch().filter("term", holding__pid=holding.pid).count() == 1

    # change the holdings first call_number
    holding["call_number"] = "cote1"
    holding = holding.update(holding, dbcommit=True, reindex=True)

    # process the bulked indexed items
    process_bulk_queue()
    ItemsSearch.flush_and_refresh()

    # ensure that the call number was correctly inherited from the holdings
    item = Item.get_record(item.id)
    assert ItemsSearch().filter("term", issue__inherited_first_call_number__raw="cote1").count() == 1
    assert ItemsSearch().filter("term", call_numbers__raw="cote1").count() == 1
    # sort_call_number must use the inherited call number when item has none
    assert ItemsSearch().filter("term", sort_call_number="cote1").count() == 1

    # set a call_number directly on the issue item: it must take priority over
    # the inherited one for sorting
    item["call_number"] = "item-own-cote"
    item.update(item, dbcommit=True, reindex=True)
    ItemsSearch.flush_and_refresh()
    assert ItemsSearch().filter("term", sort_call_number="item-own-cote").count() == 1
    assert ItemsSearch().filter("term", sort_call_number="cote1").count() == 0

    # remove the item call_number again to restore the inherited behaviour
    item.pop("call_number", None)
    item.update(item, dbcommit=True, reindex=True)
    ItemsSearch.flush_and_refresh()
    assert ItemsSearch().filter("term", sort_call_number="cote1").count() == 1

    # delete holdings first call number and change the second call_number
    holding.pop("call_number", None)
    holding["second_call_number"] = "cote2"
    holding = holding.replace(holding, dbcommit=True, reindex=True)

    # process the bulked indexed items
    process_bulk_queue()
    ItemsSearch.flush_and_refresh()

    # ensure that the call numbers were correctly inherited from the holdings
    item = Item.get_record(item.id)
    assert ItemsSearch().filter("term", issue__inherited_second_call_number__raw="cote2").count() == 1
    assert ItemsSearch().filter("term", call_numbers__raw="cote2").count() == 1
    assert ItemsSearch().filter("term", issue__inherited_first_call_number__raw="cote1").count() == 0
    assert ItemsSearch().filter("term", call_numbers__raw="cote1").count() == 0
    assert ItemsSearch().filter("term", sort_second_call_number="cote2").count() == 1
    assert ItemsSearch().filter("term", sort_call_number="cote1").count() == 0

    # clean up data ; restore the module scoped fixture record itself, as
    # `update(dbcommit=True)` returned another instance.
    holding_lib_martigny_w_patterns.update(initial_holding_data, dbcommit=True, reindex=True)
    item.delete(force=True, dbcommit=True, delindex=True)
    assert ItemsSearch().filter("term", holding__pid=holding.pid).count() == 0
