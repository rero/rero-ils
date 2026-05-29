# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""E2E tests: circulation scenario D — denied actions and unconventional workflow.

Patron A = James, Patron B = Nyota
Library A = Starfleet (item home)
Library B = Vulcan

Flow (scenarios.md):
  CHECKIN_1.1.1  Librarian A checks in on-shelf item at home lib → no action (on_shelf)
  ADD_REQUEST_1.1  James requests item (no pickup specified yet → Starfleet)
  CHECKOUT_1.2.2  Nyota tries to checkout → denied (pending is for James)
  ADD_REQUEST_1.2.2  Nyota requests item (pickup Vulcan), patron != James
  CHECKOUT_1.2.2  Nyota tries again → denied
  CHECKOUT_1.2.1  James checks out → ok (checkout patron = first PENDING patron)
  EXTEND_3.2  James tries to extend → denied (pending loan exists)
  CHECKIN_3.2.1  James returns at Vulcan → item at desk for Nyota (pickup=Vulcan=trans_lib)
  ADD_REQUEST_2.2  James requests item again (at_desk) → ok (different patron)
  CHECKOUT_2.2  Nyota tries to checkout for James' barcode → denied (patron != first pending)
  CHECKOUT_2.1  Nyota checks out → ok
  CHECKIN_3.2.2.1  Nyota returns at Vulcan; James pickup=Starfleet=item_lib → IN_TRANSIT_FOR_PICKUP
  CHECKIN_5.2.2.1  Item arrives at Vulcan (transit) → stays in transit (no action)
  CANCEL_REQUEST_5.1  James cancels → item goes IN_TRANSIT_FOR_PICKUP (to house)
  CHECKIN_5.1.2  Item arrives at Vulcan again → IN_TRANSIT_FOR_PICKUP (pending Nyota)
  CHECKIN_5.1.1  Item received at Starfleet → on shelf

Note: For simplicity, denied-action assertions verify the API returns an error status.
"""

import pytest

from .conftest import (
    LIBRARIANS,
    LOCATIONS,
    PATRONS,
    api_cancel_loan,
    api_checkin,
    api_checkout,
    api_cleanup_items_by_barcode,
    api_create_document,
    api_create_item,
    api_delete,
    api_get_patron_pid,
    api_request_for_patron,
    api_wait_for_item_status,
    wait_for_item_indexed,
)

BARCODE = "e2e-scenario-d"


@pytest.fixture(autouse=True)
def _test_data(librarian_page, base_url):
    """Create document + item; delete them after."""
    api_cleanup_items_by_barcode(librarian_page, base_url, BARCODE)
    doc_pid = api_create_document(librarian_page, base_url, " scenario-d")
    item_pid = api_create_item(librarian_page, base_url, doc_pid, BARCODE, location_pid=LOCATIONS["starfleet"])
    wait_for_item_indexed(librarian_page, base_url, BARCODE)
    yield item_pid
    api_cleanup_items_by_barcode(librarian_page, base_url, BARCODE)
    api_delete(librarian_page, base_url, "documents", doc_pid)


def _try_checkout(page, base_url, item_barcode, patron_barcode, location_pid):
    """Attempt a checkout and return the HTTP status (ok or denied)."""
    patron_pid = api_get_patron_pid(page, base_url, patron_barcode)
    resp = page.request.post(
        f"{base_url}/api/item/checkout",
        data={
            "item_barcode": item_barcode,
            "patron_pid": patron_pid,
            "transaction_location_pid": str(location_pid),
            "transaction_user_pid": LIBRARIANS["leonard"]["patron_pid"],
        },
    )
    return resp.status


def _try_extend(page, base_url, item_barcode, location_pid):
    """Attempt a loan extension and return the HTTP status."""
    resp = page.request.post(
        f"{base_url}/api/item/extend_loan",
        data={
            "item_barcode": item_barcode,
            "transaction_location_pid": str(location_pid),
            "transaction_user_pid": LIBRARIANS["leonard"]["patron_pid"],
        },
    )
    return resp.status


@pytest.mark.e2e
def test_denied_actions_and_unconventional_workflow(librarian_page, base_url, _test_data):
    """Scenario D: denied checkouts, extend blocked by pending, cancel mid-transit."""
    item_pid = _test_data

    # CHECKIN_1.1.1 — checkin on-shelf item at home library → no state change
    api_checkin(librarian_page, base_url, BARCODE, LOCATIONS["starfleet"])
    api_wait_for_item_status(librarian_page, base_url, BARCODE, "on_shelf")

    # ADD_REQUEST_1.1 — James requests, pickup at Starfleet
    api_request_for_patron(librarian_page, base_url, item_pid, PATRONS["james"]["barcode"], LOCATIONS["starfleet"])
    api_wait_for_item_status(librarian_page, base_url, BARCODE, "on_shelf")

    # CHECKOUT_1.2.2 — Nyota tries checkout → denied (first pending is James)
    status = _try_checkout(librarian_page, base_url, BARCODE, PATRONS["nyota"]["barcode"], LOCATIONS["starfleet"])
    assert status >= 400, f"Expected checkout to be denied, got {status}"
    api_wait_for_item_status(librarian_page, base_url, BARCODE, "on_shelf")

    # ADD_REQUEST_1.2.2 — Nyota also requests, pickup at Vulcan
    api_request_for_patron(librarian_page, base_url, item_pid, PATRONS["nyota"]["barcode"], LOCATIONS["vulcan"])

    # CHECKOUT_1.2.2 — Nyota tries again → still denied (first pending is James)
    status = _try_checkout(librarian_page, base_url, BARCODE, PATRONS["nyota"]["barcode"], LOCATIONS["starfleet"])
    assert status >= 400, f"Expected checkout to be denied, got {status}"

    # CHECKOUT_1.2.1 — James checks out (patron = first PENDING) → ok
    api_checkout(librarian_page, base_url, BARCODE, PATRONS["james"]["barcode"], LOCATIONS["starfleet"])
    api_wait_for_item_status(librarian_page, base_url, BARCODE, "on_loan")

    # EXTEND_3.2 — James tries to extend → denied (Nyota has pending request)
    status = _try_extend(librarian_page, base_url, BARCODE, LOCATIONS["starfleet"])
    assert status >= 400, f"Expected extend to be denied, got {status}"
    api_wait_for_item_status(librarian_page, base_url, BARCODE, "on_loan")

    # CHECKIN_3.2.1 — James returns at Vulcan; Nyota pickup=Vulcan=trans_lib → at desk
    api_checkin(librarian_page, base_url, BARCODE, LOCATIONS["vulcan"])
    api_wait_for_item_status(librarian_page, base_url, BARCODE, "at_desk")

    # ADD_REQUEST_2.2 — James requests item (at_desk for Nyota) → ok (different patron)
    api_request_for_patron(librarian_page, base_url, item_pid, PATRONS["james"]["barcode"], LOCATIONS["starfleet"])

    # CHECKOUT_2.2 — Nyota tries to checkout for James → denied (first pending is Nyota)
    status = _try_checkout(librarian_page, base_url, BARCODE, PATRONS["james"]["barcode"], LOCATIONS["vulcan"])
    assert status >= 400, f"Expected checkout to be denied, got {status}"

    # CHECKOUT_2.1 — Nyota checks out (patron = at_desk patron) → ok
    api_checkout(librarian_page, base_url, BARCODE, PATRONS["nyota"]["barcode"], LOCATIONS["vulcan"])
    api_wait_for_item_status(librarian_page, base_url, BARCODE, "on_loan")

    # CHECKIN_3.2.2.1 — Nyota returns at Vulcan; James pickup=Starfleet=item_lib, trans=Vulcan
    # → IN_TRANSIT_FOR_PICKUP (to Starfleet for James)
    api_checkin(librarian_page, base_url, BARCODE, LOCATIONS["vulcan"])
    api_wait_for_item_status(librarian_page, base_url, BARCODE, "in_transit")

    # CANCEL_REQUEST_5.1 — James cancels his request while item is in transit
    # With no other pending loan: item should go in transit to house
    api_cancel_loan(librarian_page, base_url, BARCODE, LOCATIONS["starfleet"])

    # CHECKIN_5.1.1 — Leonard receives item at Starfleet → on shelf
    api_checkin(librarian_page, base_url, BARCODE, LOCATIONS["starfleet"])
    api_wait_for_item_status(librarian_page, base_url, BARCODE, "on_shelf")
