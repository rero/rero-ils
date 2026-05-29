# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""E2E tests: circulation scenario A — standard loan at owning library.

From scenarios.md:

  A request is made on an on-shelf item with no existing requests, to be picked
  up at the owning library. Validated by the librarian. Picked up at the owning
  library and returned on time at the owning library.

Actions (scenarios.md notation):
  ADD_REQUEST_1.1  James requests item, pickup at Starfleet (owning library)
  VALIDATE_1.2     Leonard validates → ITEM_AT_DESK
  CHECKOUT_2.1     Leonard checks out to James → ITEM_ON_LOAN
  CHECKIN_3.1.1    James returns at Starfleet (item_lib = trans_lib) → on shelf

Implementation note: the patron request and checkin are done via the REST API.
Step 3 (checkout) uses the Angular professional circulation UI to verify that
the UI barcode flow correctly drives the circulation state machine.
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
    scan_patron_then_item,
    wait_for_item_indexed,
)

BARCODE = "e2e-scenario-a"


@pytest.fixture(autouse=True)
def _test_data(librarian_page, base_url):
    """Create document + item before the test; delete them after."""
    api_cleanup_items_by_barcode(librarian_page, base_url, BARCODE)
    doc_pid = api_create_document(librarian_page, base_url, " scenario-a")
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
def test_standard_loan(librarian_page, base_url, _test_data):
    """Scenario A: standard loan cycle at the item's owning library.

    ADD_REQUEST_1.1 → VALIDATE_1.2 → CHECKOUT_2.1 → CHECKIN_3.1.1
    """
    _, item_pid = _test_data

    # ADD_REQUEST_1.1 — James requests item, pickup at Starfleet (owning library)
    api_request_item(librarian_page, base_url, item_pid, pickup_location_pid=LOCATIONS["starfleet"])

    # VALIDATE_1.2 — Leonard validates → ITEM_AT_DESK (pickup lib = item lib, no transit)
    api_validate_request(librarian_page, base_url, item_pid)
    api_wait_for_item_status(librarian_page, base_url, BARCODE, "at_desk")

    # CHECKOUT_2.1 — Leonard checks out to James at Starfleet → ITEM_ON_LOAN
    go_to_circulation(librarian_page, base_url)
    scan_patron_then_item(librarian_page, PATRONS["james"]["barcode"], BARCODE)
    librarian_page.locator("[name='action-done']").wait_for(timeout=60000)
    assert "checked out" in librarian_page.locator("[name='action-done']").inner_text()

    # CHECKIN_3.1.1 — James returns at Starfleet (item_lib = trans_lib, no pending) → on shelf
    # Use the REST API directly rather than the Angular UI: the API call is simpler and not
    # sensitive to Angular bootstrap timing. All other scenarios (B-E) use api_checkin throughout.
    api_checkin(librarian_page, base_url, BARCODE, LOCATIONS["starfleet"])
    api_wait_for_item_status(librarian_page, base_url, BARCODE, "on_shelf")
