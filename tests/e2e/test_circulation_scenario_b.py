# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""E2E tests: circulation scenario B — standard loan with inter-library transit.

From scenarios.md:

  A request is made on an item of library A, on-shelf without previous requests,
  to be picked up at library B. Validated by librarian A and goes in transit.
  Received by librarian B and goes to desk. Picked up at library B. Returned on
  time at library B, goes in transit. Received at library A and goes on shelf.

Actions (scenarios.md notation):
  ADD_REQUEST_1.1  James requests item at Starfleet (A), pickup at Vulcan (B)
  VALIDATE_1.2     Leonard (A) validates → ITEM_IN_TRANSIT_FOR_PICKUP
  CHECKIN_4.1      Spock (B) receives at Vulcan → ITEM_AT_DESK
  CHECKOUT_2.1     Spock (B) checks out to James → ITEM_ON_LOAN
  CHECKIN_3.1.2    James returns at Vulcan (item_lib≠trans_lib, no pending) → ITEM_IN_TRANSIT_TO_HOUSE
  CHECKIN_5.1.1    Leonard (A) receives at Starfleet (item_lib=trans_lib) → on shelf

Library mapping: A = Starfleet (location 35, library 22), B = Vulcan (location 36, library 23)
"""

import pytest

from .conftest import (
    LOCATIONS,
    PATRONS,
    api_checkin,
    api_cleanup_items_by_barcode,
    api_create_document,
    api_create_item,
    api_delete,
    api_request_item,
    api_validate_request,
    api_wait_for_item_status,
    go_to_circulation,
    scan_barcode,
    scan_patron_then_item,
    wait_for_item_indexed,
)

BARCODE = "e2e-scenario-b"


@pytest.fixture(autouse=True)
def _test_data(librarian_page, base_url):
    """Create document + item before the test; delete them after."""
    api_cleanup_items_by_barcode(librarian_page, base_url, BARCODE)
    doc_pid = api_create_document(librarian_page, base_url, " scenario-b")
    item_pid = api_create_item(
        librarian_page,
        base_url,
        doc_pid,
        BARCODE,
        location_pid=LOCATIONS["starfleet"],
    )
    wait_for_item_indexed(librarian_page, base_url, BARCODE)
    yield doc_pid, item_pid
    api_cleanup_items_by_barcode(librarian_page, base_url, BARCODE)
    api_delete(librarian_page, base_url, "documents", doc_pid)


@pytest.mark.e2e
def test_loan_with_transit(
    librarian_page,
    spock_page,
    base_url,
    _test_data,
):
    """Scenario B: inter-library loan with transit in both directions.

    ADD_REQUEST_1.1 → VALIDATE_1.2 → CHECKIN_4.1 → CHECKOUT_2.1
    → CHECKIN_3.1.2 → CHECKIN_5.1.1
    """
    _, item_pid = _test_data

    # ADD_REQUEST_1.1 — James requests item at Starfleet, pickup at Vulcan
    api_request_item(librarian_page, base_url, item_pid, pickup_location_pid=LOCATIONS["vulcan"])

    # VALIDATE_1.2 — Leonard validates → ITEM_IN_TRANSIT_FOR_PICKUP (pickup lib ≠ item lib)
    api_validate_request(librarian_page, base_url, item_pid)
    api_wait_for_item_status(librarian_page, base_url, BARCODE, "in_transit")

    # CHECKIN_4.1 — Spock receives at Vulcan (pickup lib = trans lib) → ITEM_AT_DESK
    go_to_circulation(spock_page, base_url)
    scan_barcode(spock_page, BARCODE)
    spock_page.locator("[name='action-done']").wait_for(timeout=60000)
    assert "receive" in spock_page.locator("[name='action-done']").inner_text()

    # CHECKOUT_2.1 — Spock checks out to James at Vulcan → ITEM_ON_LOAN
    go_to_circulation(spock_page, base_url)
    scan_patron_then_item(spock_page, PATRONS["james"]["barcode"], BARCODE)
    spock_page.locator("[name='action-done']").wait_for(timeout=60000)
    assert "checked out" in spock_page.locator("[name='action-done']").inner_text()

    # CHECKIN_3.1.2 — James returns at Vulcan (item_lib=Starfleet ≠ Vulcan=trans_lib, no pending)
    # → ITEM_IN_TRANSIT_TO_HOUSE
    go_to_circulation(spock_page, base_url)
    scan_barcode(spock_page, BARCODE)
    spock_page.locator("[name='action-done']").wait_for(timeout=60000)
    assert "checked in" in spock_page.locator("[name='action-done']").inner_text()
    api_wait_for_item_status(spock_page, base_url, BARCODE, "in_transit")

    # CHECKIN_5.1.1 — Leonard receives at Starfleet (item_lib = trans_lib, no pending) → on shelf
    # Use the REST API directly rather than the Angular UI: simpler and not sensitive to Angular
    # bootstrap timing.
    api_checkin(librarian_page, base_url, BARCODE, LOCATIONS["starfleet"])
    api_wait_for_item_status(librarian_page, base_url, BARCODE, "on_shelf")
