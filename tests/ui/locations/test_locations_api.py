# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Location Record tests."""

from copy import deepcopy
from unittest import mock

import pytest
from elasticsearch.exceptions import NotFoundError

from rero_ils.modules.documents.api import DocumentsIndexer, DocumentsSearch
from rero_ils.modules.items.api import Item, ItemsIndexer, ItemsSearch
from rero_ils.modules.items.models import ItemIssueStatus
from rero_ils.modules.locations.api import Location, LocationsSearch
from rero_ils.modules.tasks import process_bulk_queue
from rero_ils.modules.utils import get_ref_for_pid


def test_location_cannot_delete(item_lib_martigny):
    """Test cannot delete."""
    location_pid = item_lib_martigny.location_pid
    location = Location.get_record_by_pid(location_pid)
    can, reasons = location.can_delete
    assert not can
    assert reasons["links"]["holdings"] == 1
    assert reasons["links"]["items"] == 1


def test_location_organisation_pid(org_martigny, loc_public_martigny):
    """Test organisation pid has been added during the indexing."""
    location = LocationsSearch().get_record_by_pid(loc_public_martigny.pid)
    assert location.organisation.pid == org_martigny.pid


def test_location_restrict_pickup(
    loc_public_martigny,
    loc_restricted_martigny,
    loc_public_saxon,
    loc_public_martigny_data,
    loc_restricted_martigny_data,
    loc_public_saxon_data,
):
    """Test automatic modification of restrict_pickup_to field."""
    loc_m1 = loc_public_martigny
    loc_m2 = loc_restricted_martigny
    loc_sax = loc_public_saxon

    # STEP 1 :: Init location for test
    #   * ensure `loc_m2` and `loc_sax` are pickup locations
    #   * ensure `loc_m1` defines other location as pickup restriction
    loc_m1["restrict_pickup_to"] = [
        {"$ref": get_ref_for_pid(Location, loc_m2.pid)},
        {"$ref": get_ref_for_pid(Location, loc_sax.pid)},
    ]
    loc_m1 = loc_m1.update(loc_m1, dbcommit=True, reindex=True)
    loc_m2["is_pickup"] = True
    loc_m2["pickup_name"] = "loc_m2_pickup"
    loc_m2 = loc_m2.update(loc_m2, dbcommit=True, reindex=True)
    loc_sax["is_pickup"] = True
    loc_sax["pickup_name"] = "loc_sax_pickup"
    loc_sax = loc_sax.update(loc_sax, dbcommit=True, reindex=True)
    LocationsSearch.flush_and_refresh()

    assert len(LocationsSearch().get_record_by_pid(loc_m1.pid).to_dict()["restrict_pickup_to"]) == 2

    # STEP 2 :: Define that loc_m2 isn't yet a pickup location
    #   The `loc_m1` must now only contain `loc_sax` as restriction for
    #   pickup location. search index should also reflect this change.
    del loc_m2["is_pickup"]
    loc_m2 = loc_m2.update(loc_m2, dbcommit=True, reindex=True)
    loc_m1 = Location.get_record(loc_m1.id)
    assert loc_m1.restrict_pickup_to == [loc_sax.pid]
    LocationsSearch.flush_and_refresh()
    search_restrictions = [
        restriction_loc.pid for restriction_loc in LocationsSearch().get_record_by_pid(loc_m1.pid).restrict_pickup_to
    ]
    assert search_restrictions == [loc_sax.pid]

    # STEP 3 :: Define that loc_sax isn't yet a pickup location
    #   The `loc_m1` must not contain any restriction for pickup location.
    #   search index should reflect this change`
    del loc_sax["is_pickup"]
    loc_sax = loc_sax.update(loc_sax, dbcommit=True, reindex=True)
    assert "pickup_name" not in loc_sax
    loc_m1 = Location.get_record(loc_m1.id)
    assert not loc_m1.restrict_pickup_to
    LocationsSearch.flush_and_refresh()
    assert "restrict_pickup_to" not in LocationsSearch().get_record_by_pid(loc_sax.pid).to_dict()

    # Reset fixtures
    loc_m1.update(loc_public_martigny_data, dbcommit=True, reindex=True)
    loc_m2.update(loc_restricted_martigny_data, dbcommit=True, reindex=True)
    loc_sax.update(loc_public_saxon_data, dbcommit=True, reindex=True)


@pytest.mark.parametrize("reference", ["location", "temporary_location"])
def test_location_online_flag_refreshes_documents(
    holding_lib_martigny_w_patterns,
    holding_lib_martigny_w_patterns_data,
    loc_online_martigny,
    reference,
):
    """Refresh each document once, even while item indexing is queued."""
    holding = holding_lib_martigny_w_patterns
    location = loc_online_martigny
    initial_location = deepcopy(dict(location))
    items = []
    try:
        location["is_online"] = False
        location.update(location, dbcommit=True, reindex=True)
        items = [
            holding.create_regular_issue(status=ItemIssueStatus.RECEIVED, dbcommit=True, reindex=True) for _ in range(2)
        ]
        if reference == "location":
            holding["location"] = {"$ref": get_ref_for_pid("loc", location.pid)}
            with mock.patch("rero_ils.modules.holdings.listener.process_bulk_queue.apply_async"):
                holding.update(holding, dbcommit=True, reindex=True)
            assert ItemsSearch().filter("term", location__pid=location.pid).count() == 0
        else:
            for item in items:
                item["temporary_location"] = {"$ref": get_ref_for_pid("loc", location.pid)}
                item.update(item, dbcommit=True, reindex=False)
            ItemsIndexer().bulk_index([item.id for item in items])
            assert ItemsSearch().filter("term", temporary_location__pid=location.pid).count() == 0

        document = holding.document
        for is_online in (True, False):
            with (
                mock.patch.object(DocumentsIndexer, "bulk_index", wraps=DocumentsIndexer().bulk_index) as bulk_index,
                mock.patch("rero_ils.modules.tasks.process_bulk_queue.apply_async"),
            ):
                location["is_online"] = is_online
                location.update(location, dbcommit=True, reindex=True)
                bulk_index.assert_called_once()
                assert list(bulk_index.call_args.args[0]) == [document.id]
            process_bulk_queue()
            DocumentsSearch.flush_and_refresh()
            indexed = DocumentsSearch().get_record_by_pid(document.pid)
            assert indexed["has_online_item"] is is_online
            assert indexed["has_physical_resources"] == (not is_online)
    finally:
        location.update(initial_location, dbcommit=True, reindex=True)
        holding.update(holding_lib_martigny_w_patterns_data, dbcommit=True, reindex=True)
        process_bulk_queue()
        for item in items:
            Item.get_record(item.id).delete(force=True, dbcommit=True, delindex=True)


def test_location_name_change_does_not_refresh_documents(loc_public_martigny):
    """A name edit must not schedule document reindexing."""
    location = loc_public_martigny
    initial_name = location["name"]
    try:
        with mock.patch("rero_ils.modules.locations.api.reindex_location_documents") as refresh:
            location["name"] = f"{initial_name} renamed"
            location.update(location, dbcommit=True, reindex=True)
            refresh.delay.assert_not_called()
    finally:
        location["name"] = initial_name
        location.update(location, dbcommit=True, reindex=True)


@pytest.mark.parametrize(("old_flag", "new_flag"), [(None, False), (False, None)])
def test_location_missing_online_flag_is_false(loc_public_martigny, old_flag, new_flag):
    """An absent online flag and an explicit false flag are equivalent."""
    location = loc_public_martigny
    initial_location = deepcopy(dict(location))
    try:
        if old_flag is None:
            location.pop("is_online", None)
        else:
            location["is_online"] = old_flag
        location.update(location, dbcommit=True, reindex=True)
        with mock.patch("rero_ils.modules.locations.api.reindex_location_documents") as refresh:
            if new_flag is None:
                location.pop("is_online", None)
            else:
                location["is_online"] = new_flag
            location.update(location, dbcommit=True, reindex=True)
            refresh.delay.assert_not_called()
    finally:
        location.update(initial_location, dbcommit=True, reindex=True)


def test_location_missing_index_refreshes_documents(loc_public_martigny):
    """Rebuild affected document classifications when the old index entry is missing."""
    location = loc_public_martigny
    with (
        mock.patch(
            "rero_ils.modules.locations.api.current_search_client.get",
            side_effect=NotFoundError(404, "location missing"),
        ),
        mock.patch("rero_ils.modules.locations.api.reindex_location_documents") as refresh,
    ):
        location.reindex()
        refresh.delay.assert_called_once_with(location.pid)
