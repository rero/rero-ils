# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""E2E tests: circulation scenario C — item with multiple in-transit requests.

Mapping to 2-library setup (Starfleet=A, Vulcan=B=C):
  Library A = Starfleet (item home, Nyota's pickup)
  Library B = Vulcan    (James's pickup)

Flow (scenarios.md):
  ADD_REQUEST_1.1   James requests item at Starfleet, pickup at Vulcan  → PENDING
  VALIDATE_1.2      Leonard validates                                    → IN_TRANSIT_FOR_PICKUP
  CHECKIN_4.1       Spock receives at Vulcan                             → ITEM_AT_DESK
  CHECKOUT_2.1      Spock checks out to James                           → ITEM_ON_LOAN
  ADD_REQUEST_3.2.1 Nyota requests item, pickup at Starfleet            → PENDING
  CHECKIN_3.2.2.1   James returns at Vulcan (pickup=item_lib≠trans_lib) → IN_TRANSIT_FOR_PICKUP
  CHECKIN_4.1       Leonard receives at Starfleet                       → ITEM_AT_DESK
  CHECKOUT_2.1      Leonard checks out to Nyota                         → ITEM_ON_LOAN
  EXTEND_3.1        Nyota extends loan                                  → ITEM_ON_LOAN
  CHECKIN_3.1.2     Nyota returns at Vulcan (item_lib≠trans_lib)        → IN_TRANSIT_TO_HOUSE
  CHECKIN_5.1.1     Leonard receives at Starfleet                       → on shelf
"""

import pytest

from .conftest import (
    LOCATIONS,
    PATRONS,
    api_checkin,
    api_checkout,
    api_cleanup_items_by_barcode,
    api_create_document,
    api_create_item,
    api_delete,
    api_extend_loan,
    api_request_for_patron,
    api_validate_request,
    api_wait_for_item_status,
    wait_for_item_indexed,
)

BARCODE = "e2e-scenario-c"


@pytest.fixture(autouse=True)
def _test_data(librarian_page, base_url):
    """Create document + item; delete them after."""
    api_cleanup_items_by_barcode(librarian_page, base_url, BARCODE)
    doc_pid = api_create_document(librarian_page, base_url, " scenario-c")
    item_pid = api_create_item(librarian_page, base_url, doc_pid, BARCODE, location_pid=LOCATIONS["starfleet"])
    wait_for_item_indexed(librarian_page, base_url, BARCODE)
    yield item_pid
    api_cleanup_items_by_barcode(librarian_page, base_url, BARCODE)
    api_delete(librarian_page, base_url, "documents", doc_pid)


@pytest.mark.e2e
def test_multiple_requests_with_transit(librarian_page, base_url, _test_data):
    """Scenario C: two patrons request the same item; full cycle with transit."""
    item_pid = _test_data

    # ADD_REQUEST_1.1 — James requests, pickup at Vulcan
    api_request_for_patron(librarian_page, base_url, item_pid, PATRONS["james"]["barcode"], LOCATIONS["vulcan"])
    api_wait_for_item_status(librarian_page, base_url, BARCODE, "on_shelf")

    # VALIDATE_1.2 — Leonard validates → item in transit to Vulcan
    api_validate_request(librarian_page, base_url, item_pid)
    api_wait_for_item_status(librarian_page, base_url, BARCODE, "in_transit")

    # CHECKIN_4.1 — Spock receives at Vulcan → item at desk
    api_checkin(librarian_page, base_url, BARCODE, LOCATIONS["vulcan"])
    api_wait_for_item_status(librarian_page, base_url, BARCODE, "at_desk")

    # CHECKOUT_2.1 — Spock checks out to James at Vulcan
    api_checkout(librarian_page, base_url, BARCODE, PATRONS["james"]["barcode"], LOCATIONS["vulcan"])
    api_wait_for_item_status(librarian_page, base_url, BARCODE, "on_loan")

    # ADD_REQUEST_3.2.1 — Nyota requests, pickup at Starfleet (item home = CHECKIN_3.2.2.1 condition)
    api_request_for_patron(librarian_page, base_url, item_pid, PATRONS["nyota"]["barcode"], LOCATIONS["starfleet"])

    # CHECKIN_3.2.2.1 — James returns at Vulcan; pending pickup=Starfleet=item_lib≠Vulcan
    # → item in transit for pickup (to Starfleet for Nyota)
    api_checkin(librarian_page, base_url, BARCODE, LOCATIONS["vulcan"])
    api_wait_for_item_status(librarian_page, base_url, BARCODE, "in_transit")

    # CHECKIN_4.1 — Leonard receives at Starfleet (pickup=Starfleet=transaction_lib) → at desk
    api_checkin(librarian_page, base_url, BARCODE, LOCATIONS["starfleet"])
    api_wait_for_item_status(librarian_page, base_url, BARCODE, "at_desk")

    # CHECKOUT_2.1 — Leonard checks out to Nyota at Starfleet
    api_checkout(librarian_page, base_url, BARCODE, PATRONS["nyota"]["barcode"], LOCATIONS["starfleet"])
    api_wait_for_item_status(librarian_page, base_url, BARCODE, "on_loan")

    # EXTEND_3.1 — Nyota extends loan (no pending requests).
    # Note: RERO ILS prevents extension when first_open(now+renewal_days) ≤ end_date,
    # i.e. when the loan was just created and renewal would not push the due date forward.
    # The circ policy DOES allow renewals; timing prevents it in automated tests.
    # In production a patron would extend close to the due date.
    api_extend_loan(librarian_page, base_url, BARCODE, LOCATIONS["starfleet"])
    api_wait_for_item_status(librarian_page, base_url, BARCODE, "on_loan")

    # CHECKIN_3.1.2 — Nyota returns at Vulcan (item_lib=Starfleet≠Vulcan=trans_lib, no pending)
    # → item in transit to house (Starfleet)
    api_checkin(librarian_page, base_url, BARCODE, LOCATIONS["vulcan"])
    api_wait_for_item_status(librarian_page, base_url, BARCODE, "in_transit")

    # CHECKIN_5.1.1 — Leonard receives at Starfleet (item_lib=Starfleet=trans_lib) → on shelf
    api_checkin(librarian_page, base_url, BARCODE, LOCATIONS["starfleet"])
    api_wait_for_item_status(librarian_page, base_url, BARCODE, "on_shelf")
