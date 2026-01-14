# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021-2026 RERO
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

"""Tests circulation operation for item with temporary item_type."""

from datetime import datetime, timedelta

import ciso8601
from flask import url_for
from invenio_accounts.testutils import login_user_via_session

from rero_ils.modules.circ_policies.api import CircPolicy
from rero_ils.modules.item_types.api import ItemTypesSearch
from rero_ils.modules.items.api import Item, ItemsSearch
from rero_ils.modules.items.models import ItemStatus
from rero_ils.modules.patrons.api import PatronsSearch
from rero_ils.modules.utils import get_ref_for_pid
from tests.utils import get_json, postdata


def test_checkout_temporary_item_type(
    client,
    document,
    librarian_martigny,
    lib_martigny,
    loc_public_martigny,
    patron_martigny,
    item_lib_martigny,
    item_type_on_site_martigny,
    circ_policy_short_martigny,
    circ_policy_default_martigny,
):
    """Test checkout or item with temporary item_types"""
    login_user_via_session(client, librarian_martigny.user)
    item = item_lib_martigny
    assert item.status == ItemStatus.ON_SHELF

    # test basic behavior
    cipo_used = CircPolicy.provide_circ_policy(
        lib_martigny.organisation_pid,
        lib_martigny.pid,
        patron_martigny.patron_type_pid,
        item.item_type_circulation_category_pid,
    )
    assert cipo_used == circ_policy_short_martigny

    # add a temporary_item_type on item
    #   due to this change, the cipo used during circulation operation should
    #   be different from the first cipo found.
    item["temporary_item_type"] = {"$ref": get_ref_for_pid("itty", item_type_on_site_martigny.pid)}
    item = item.update(data=item, dbcommit=True, reindex=True)
    ItemsSearch.flush_and_refresh()

    # check temporary_circulation_category is indexed in document
    doc_list = url_for(
        "invenio_records_rest.doc_list",
        q=f"holdings.circulation_category.pid\
                :{item_type_on_site_martigny.pid}",
    )
    res = client.get(doc_list)
    data = get_json(res)
    assert len(data["hits"]["hits"]) == 1

    cipo_tmp_used = CircPolicy.provide_circ_policy(
        lib_martigny.organisation_pid,
        lib_martigny.pid,
        patron_martigny.patron_type_pid,
        item.item_type_circulation_category_pid,
    )
    assert cipo_tmp_used == circ_policy_default_martigny

    delta = timedelta(cipo_tmp_used.get("checkout_duration"))
    expected_date = datetime.now() + delta
    expected_dates = [expected_date, lib_martigny.next_open(expected_date)]
    expected_dates = [d.strftime("%Y-%m-%d") for d in expected_dates]

    # try a checkout and check the transaction end_date is related to the cipo
    # corresponding to the temporary item_type
    params = {
        "item_pid": item.pid,
        "patron_pid": patron_martigny.pid,
        "transaction_user_pid": librarian_martigny.pid,
        "transaction_location_pid": loc_public_martigny.pid,
    }
    res, data = postdata(client, "api_item.checkout", params)
    assert res.status_code == 200
    transaction_end_date = data["action_applied"]["checkout"]["end_date"]
    transaction_end_date = ciso8601.parse_datetime(transaction_end_date).date()
    transaction_end_date = transaction_end_date.strftime("%Y-%m-%d")
    assert transaction_end_date in expected_dates

    # checkin the item to reset its status for other tests
    checkin_params = {
        "item_barcode": item.get("barcode"),
        "transaction_library_pid": lib_martigny.pid,
        "transaction_user_pid": librarian_martigny.pid,
    }
    res, data = postdata(client, "api_item.checkin", checkin_params)
    assert res.status_code == 200

    # reset the item to original value
    item.pop("temporary_item_type", None)
    item.update(data=item, dbcommit=True, reindex=True)
    ItemsSearch.flush_and_refresh()


def test_checkout_remove_temporary_item_type_on_scan(
    client,
    document,
    librarian_martigny,
    lib_martigny,
    loc_public_martigny,
    patron_martigny,
    item_lib_martigny,
    item_type_on_site_martigny,
    circ_policy_short_martigny,
):
    """Test checkout removes temporary item type when remove_on_scan is enabled."""
    item = item_lib_martigny
    assert item.status == ItemStatus.ON_SHELF

    # Enable remove_temporary_item_type_on_scan on the item type
    item_type_on_site_martigny["remove_temporary_item_type_on_scan"] = True
    item_type_on_site_martigny.update(item_type_on_site_martigny, dbcommit=True, reindex=True)
    ItemTypesSearch.flush_and_refresh()

    # Add temporary_item_type to item
    item["temporary_item_type"] = {"$ref": get_ref_for_pid("itty", item_type_on_site_martigny.pid)}
    item = item.update(data=item, dbcommit=True, reindex=True)
    ItemsSearch.flush_and_refresh()
    assert item.get("temporary_item_type")

    # Get the circulation policy that should be used (main item type, not temporary)
    cipo_main = CircPolicy.provide_circ_policy(
        lib_martigny.organisation_pid,
        lib_martigny.pid,
        patron_martigny.patron_type_pid,
        item.item_type_pid,
    )
    assert cipo_main == circ_policy_short_martigny

    delta = timedelta(cipo_main.get("checkout_duration"))
    expected_date = datetime.now() + delta
    expected_dates = [expected_date, lib_martigny.next_open(expected_date)]
    expected_dates = [d.strftime("%Y-%m-%d") for d in expected_dates]

    # Perform checkout
    login_user_via_session(client, librarian_martigny.user)
    params = {
        "item_pid": item.pid,
        "patron_pid": patron_martigny.pid,
        "transaction_user_pid": librarian_martigny.pid,
        "transaction_location_pid": loc_public_martigny.pid,
    }
    res, data = postdata(client, "api_item.checkout", params)
    assert res.status_code == 200
    assert "removed_temporary_item_type" in data
    assert data["removed_temporary_item_type"]["name"] == item_type_on_site_martigny.get("name")

    # Check that the circulation policy used was the main item type policy
    transaction_end_date = data["action_applied"]["checkout"]["end_date"]
    transaction_end_date = ciso8601.parse_datetime(transaction_end_date).date()
    transaction_end_date = transaction_end_date.strftime("%Y-%m-%d")
    assert transaction_end_date in expected_dates

    # Reload item and verify temporary_item_type was removed
    item = Item.get_record_by_pid(item.pid)
    assert item.get("temporary_item_type") is None

    # Checkin the item to reset its status for other tests
    checkin_params = {
        "item_barcode": item.get("barcode"),
        "transaction_library_pid": lib_martigny.pid,
        "transaction_user_pid": librarian_martigny.pid,
    }
    res, data = postdata(client, "api_item.checkin", checkin_params)
    assert res.status_code == 200
    ItemsSearch.flush_and_refresh()

    # Cleanup: reset item_type setting
    item_type_on_site_martigny.pop("remove_temporary_item_type_on_scan", None)
    item_type_on_site_martigny.update(item_type_on_site_martigny, dbcommit=True, reindex=True)
    ItemTypesSearch.flush_and_refresh()


def test_checkin_remove_temporary_item_type_on_scan(
    client,
    document,
    librarian_martigny,
    lib_martigny,
    loc_public_martigny,
    patron_martigny,
    item_lib_martigny,
    item_type_on_site_martigny,
):
    """Test checkin removes temporary item type when remove_on_scan is enabled."""

    item = item_lib_martigny
    assert item.status == ItemStatus.ON_SHELF

    # First, checkout the item
    login_user_via_session(client, librarian_martigny.user)
    params = {
        "item_pid": item.pid,
        "patron_pid": patron_martigny.pid,
        "transaction_user_pid": librarian_martigny.pid,
        "transaction_location_pid": loc_public_martigny.pid,
    }
    res, data = postdata(client, "api_item.checkout", params)
    assert res.status_code == 200

    # Reload item to get updated status
    item = Item.get_record_by_pid(item.pid)
    assert item.status == ItemStatus.ON_LOAN

    # Enable remove_temporary_item_type_on_scan and add temporary_item_type
    item_type_on_site_martigny["remove_temporary_item_type_on_scan"] = True
    item_type_on_site_martigny.update(item_type_on_site_martigny, dbcommit=True, reindex=True)
    ItemTypesSearch.flush_and_refresh()

    item["temporary_item_type"] = {"$ref": get_ref_for_pid("itty", item_type_on_site_martigny.pid)}
    item = item.update(data=item, dbcommit=True, reindex=True)
    ItemsSearch.flush_and_refresh()
    assert item.get("temporary_item_type")

    # Perform checkin
    params = {
        "item_barcode": item.get("barcode"),
        "transaction_library_pid": lib_martigny.pid,
        "transaction_user_pid": librarian_martigny.pid,
    }
    res, data = postdata(client, "api_item.checkin", params)
    assert res.status_code == 200

    # Check that response contains removed_temporary_item_type info
    assert "removed_temporary_item_type" in data
    assert data["removed_temporary_item_type"]["name"] == item_type_on_site_martigny.get("name")

    # Reload item and verify temporary_item_type was removed
    item = Item.get_record_by_pid(item.pid)
    assert item.get("temporary_item_type") is None

    # Cleanup: reset item_type setting
    item_type_on_site_martigny.pop("remove_temporary_item_type_on_scan", None)
    item_type_on_site_martigny.update(item_type_on_site_martigny, dbcommit=True, reindex=True)
    ItemTypesSearch.flush_and_refresh()


def test_remove_temporary_item_type_on_scan_disabled(
    client,
    document,
    librarian_martigny,
    lib_martigny,
    loc_public_martigny,
    patron_martigny,
    item_lib_martigny,
    item_type_on_site_martigny,
):
    """Test that temporary item type is NOT removed when remove_on_scan is disabled."""

    item = item_lib_martigny
    assert item.status == ItemStatus.ON_SHELF

    # Make sure remove_temporary_item_type_on_scan is disabled
    item_type_on_site_martigny["remove_temporary_item_type_on_scan"] = False
    item_type_on_site_martigny.update(item_type_on_site_martigny, dbcommit=True, reindex=True)
    ItemTypesSearch.flush_and_refresh()

    # Add temporary_item_type to item
    item["temporary_item_type"] = {"$ref": get_ref_for_pid("itty", item_type_on_site_martigny.pid)}
    item = item.update(data=item, dbcommit=True, reindex=True)
    ItemsSearch.flush_and_refresh()
    assert item.get("temporary_item_type") is not None

    # Perform checkout
    login_user_via_session(client, librarian_martigny.user)
    params = {
        "item_pid": item.pid,
        "patron_pid": patron_martigny.pid,
        "transaction_user_pid": librarian_martigny.pid,
        "transaction_location_pid": loc_public_martigny.pid,
    }
    res, data = postdata(client, "api_item.checkout", params)
    assert res.status_code == 200

    # Check that response does NOT contain removed_temporary_item_type info
    assert "removed_temporary_item_type" not in data

    # Reload item and verify temporary_item_type is still present
    item = Item.get_record_by_pid(item.pid)
    assert item.get("temporary_item_type") is not None

    # Checkin the item to reset its status for other tests
    checkin_params = {
        "item_barcode": item.get("barcode"),
        "transaction_library_pid": lib_martigny.pid,
        "transaction_user_pid": librarian_martigny.pid,
    }
    res, data = postdata(client, "api_item.checkin", checkin_params)
    assert res.status_code == 200
    ItemsSearch.flush_and_refresh()

    # Cleanup: remove temporary_item_type and reset item_type setting
    item = Item.get_record_by_pid(item.pid)
    item.pop("temporary_item_type", None)
    item.update(data=item, dbcommit=True, reindex=True)
    ItemsSearch.flush_and_refresh()
    item_type_on_site_martigny.pop("remove_temporary_item_type_on_scan", None)
    item_type_on_site_martigny.update(item_type_on_site_martigny, dbcommit=True, reindex=True)
    ItemTypesSearch.flush_and_refresh()


def test_no_circulation_action_remove_temporary_item_type_on_scan(
    client,
    librarian_martigny,
    lib_martigny,
    item_lib_martigny,
    item_type_on_site_martigny,
):
    """Test that temporary item type is removed even when no circulation action occurs."""

    item = item_lib_martigny
    assert item.status == ItemStatus.ON_SHELF

    # Enable remove_temporary_item_type_on_scan on the item type
    item_type_on_site_martigny["remove_temporary_item_type_on_scan"] = True
    item_type_on_site_martigny.update(item_type_on_site_martigny, dbcommit=True, reindex=True)
    ItemTypesSearch.flush_and_refresh()

    # Add temporary_item_type to item
    item["temporary_item_type"] = {"$ref": get_ref_for_pid("itty", item_type_on_site_martigny.pid)}
    item = item.update(data=item, dbcommit=True, reindex=True)
    ItemsSearch.flush_and_refresh()
    assert item.get("temporary_item_type") is not None

    # Try to checkin an item that is already on shelf (no circulation action)
    login_user_via_session(client, librarian_martigny.user)
    params = {
        "item_barcode": item.get("barcode"),
        "transaction_library_pid": lib_martigny.pid,
        "transaction_user_pid": librarian_martigny.pid,
    }
    res, data = postdata(client, "api_item.checkin", params)
    # Should return 400 because no circulation action is possible
    assert res.status_code == 400

    # But should still contain removed_temporary_item_type info
    assert "removed_temporary_item_type" in data
    assert data["removed_temporary_item_type"]["name"] == item_type_on_site_martigny.get("name")

    # Reload item and verify temporary_item_type was removed
    item = Item.get_record_by_pid(item.pid)
    assert item.get("temporary_item_type") is None

    # Cleanup: reset item_type setting
    item_type_on_site_martigny.pop("remove_temporary_item_type_on_scan", None)
    item_type_on_site_martigny.update(item_type_on_site_martigny, dbcommit=True, reindex=True)
    ItemTypesSearch.flush_and_refresh()


def test_circulation_exception_remove_temporary_item_type_on_scan(
    client,
    librarian_martigny,
    lib_martigny,
    loc_public_martigny,
    patron_martigny,
    item_lib_martigny,
    item_type_on_site_martigny,
):
    """Test that temporary item type is removed even when CirculationException occurs."""

    item = item_lib_martigny
    patron = patron_martigny

    # Enable remove_temporary_item_type_on_scan on the item type
    item_type_on_site_martigny["remove_temporary_item_type_on_scan"] = True
    item_type_on_site_martigny.update(item_type_on_site_martigny, dbcommit=True, reindex=True)
    ItemTypesSearch.flush_and_refresh()

    # Add temporary_item_type to item
    item["temporary_item_type"] = {"$ref": get_ref_for_pid("itty", item_type_on_site_martigny.pid)}
    item = item.update(data=item, dbcommit=True, reindex=True)
    ItemsSearch.flush_and_refresh()
    assert item.get("temporary_item_type") is not None

    # Block the patron to cause CirculationException
    patron.setdefault("patron", {})["blocked"] = True
    patron = patron.update(data=patron, dbcommit=True, reindex=True)
    PatronsSearch.flush_and_refresh()

    # Try to checkout - should fail with CirculationException (403)
    login_user_via_session(client, librarian_martigny.user)
    params = {
        "item_pid": item.pid,
        "patron_pid": patron.pid,
        "transaction_user_pid": librarian_martigny.pid,
        "transaction_location_pid": loc_public_martigny.pid,
    }
    res, data = postdata(client, "api_item.checkout", params)
    assert res.status_code == 403
    assert "message" in data
    assert "blocked" in data["message"]

    # Check that response contains removed_temporary_item_type info
    assert "removed_temporary_item_type" in data
    assert data["removed_temporary_item_type"]["name"] == item_type_on_site_martigny.get("name")

    # Reload item and verify temporary_item_type was removed
    item = Item.get_record_by_pid(item.pid)
    assert item.get("temporary_item_type") is None

    # Cleanup: unblock patron and reset item_type setting
    patron["patron"].pop("blocked", None)
    patron.update(data=patron, dbcommit=True, reindex=True)
    PatronsSearch.flush_and_refresh()
    item_type_on_site_martigny.pop("remove_temporary_item_type_on_scan", None)
    item_type_on_site_martigny.update(item_type_on_site_martigny, dbcommit=True, reindex=True)
    ItemTypesSearch.flush_and_refresh()
