# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""E2E tests: circulation scenario E — complex multi-patron workflow with cancellations.

User A = James (barcode e2e-test-1), User B = Nyota (barcode e2e-test-2)
Library A = Starfleet (item home), Library B = Vulcan

Flow (scenarios.md):
  ADD_REQUEST_1.1    User B (Nyota) requests, pickup at Vulcan              → PENDING
  CHECKIN_1.2.2      Librarian A checks in item (pending pickup=Vulcan≠home) → IN_TRANSIT_FOR_PICKUP
  CHECKIN_4.2        Librarian C checks item in (transit, pickup≠trans_lib)  → stays in transit
  ADD_REQUEST_4.1    User B tries to request again                           → denied (already requested)
  ADD_REQUEST_4.2    User A requests, pickup at Starfleet                    → PENDING
  CHECKOUT_4.2       Librarian B tries checkout for User A                   → denied (first pending=Nyota)
  CHECKOUT_4.1       User B (Nyota) requests checkout at Vulcan              → ok (patron=first pending)
  ADD_REQUEST_3.2.2.1  User A tries to request again                         → denied (already has pending)
  ADD_REQUEST_3.2.2.2  User C (third patron) tries to request                → ok (different patron)
       [simplified: skipped — only 2 test patrons available]
  CHECKOUT_3.2       User B returns item; User A pickup=Starfleet=item_lib   → IN_TRANSIT_FOR_PICKUP
       [simplified as: Nyota returns; James's pickup=Starfleet=item_lib]
  CHANGE_PICKUP_LOCATION_4  User A changes pickup to Vulcan
  CANCEL_REQUEST_4.1.2  User A cancels → item goes IN_TRANSIT_FOR_PICKUP (next pending)
       [simplified: no next pending → item goes IN_TRANSIT_TO_HOUSE]
  CHECKOUT_5.1       User B finds item at Vulcan and borrows it              → ITEM_ON_LOAN
  CHECKIN_3.1.1      User B returns at Starfleet (item home = trans lib)     → on shelf
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

BARCODE = "e2e-scenario-e"


@pytest.fixture(autouse=True)
def _test_data(librarian_page, base_url):
    """Create document + item; delete them after."""
    api_cleanup_items_by_barcode(librarian_page, base_url, BARCODE)
    doc_pid = api_create_document(librarian_page, base_url, " scenario-e")
    item_pid = api_create_item(librarian_page, base_url, doc_pid, BARCODE, location_pid=LOCATIONS["starfleet"])
    wait_for_item_indexed(librarian_page, base_url, BARCODE)
    yield item_pid
    api_cleanup_items_by_barcode(librarian_page, base_url, BARCODE)
    api_delete(librarian_page, base_url, "documents", doc_pid)


def _try_checkout(page, base_url, item_barcode, patron_barcode, location_pid):
    """Attempt checkout and return HTTP status."""
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


def _try_request(page, base_url, item_pid, patron_barcode, pickup_location_pid):
    """Attempt a patron request and return HTTP status."""
    patron_pid = api_get_patron_pid(page, base_url, patron_barcode)
    resp = page.request.post(
        f"{base_url}/api/item/request",
        data={
            "item_pid": item_pid,
            "pickup_location_pid": str(pickup_location_pid),
            "patron_pid": patron_pid,
            "transaction_location_pid": str(LOCATIONS["starfleet"]),
            "transaction_user_pid": LIBRARIANS["leonard"]["patron_pid"],
        },
    )
    return resp.status


def _update_pickup_location(page, base_url, item_barcode, new_pickup_location_pid):
    """Change the pickup location of an active loan for the item.

    After an automatic validation, the loan may be ITEM_IN_TRANSIT_FOR_PICKUP
    rather than PENDING (CHANGE_PICKUP_LOCATION_4 applies to both states).
    """
    item_resp = page.request.get(f"{base_url}/api/items/", params={"q": f"barcode:{item_barcode}"})
    item_pid = item_resp.json()["hits"]["hits"][0]["metadata"]["pid"]
    loans_resp = page.request.get(
        f"{base_url}/api/loans/",
        params={"q": f"item_pid.value:{item_pid} AND state:(PENDING OR ITEM_IN_TRANSIT_FOR_PICKUP)"},
    )
    hits = loans_resp.json().get("hits", {}).get("hits", [])
    assert hits, f"No active loan found for item {item_barcode!r} — cannot update pickup location"
    loan_pid = hits[0]["metadata"]["pid"]
    # The endpoint uses do_loan_jsonify_action which requires JSON and 'pid' (not 'loan_pid')
    resp = page.request.post(
        f"{base_url}/api/item/update_loan_pickup_location",
        data={"pid": loan_pid, "pickup_location_pid": str(new_pickup_location_pid)},
        headers={"Content-Type": "application/json"},
    )
    assert resp.ok, f"update_loan_pickup_location failed: {resp.status} {resp.json()}"


@pytest.mark.e2e
def test_complex_workflow_with_cancellations(librarian_page, base_url, _test_data):
    """Scenario E: multi-step workflow with denials, transit, and mid-cycle cancellations."""
    item_pid = _test_data

    # ADD_REQUEST_1.1 — Nyota requests item, pickup at Vulcan
    api_request_for_patron(librarian_page, base_url, item_pid, PATRONS["nyota"]["barcode"], LOCATIONS["vulcan"])
    api_wait_for_item_status(librarian_page, base_url, BARCODE, "on_shelf")

    # CHECKIN_1.2.2 — Librarian checkin at Starfleet; pending pickup=Vulcan≠Starfleet
    # → item goes IN_TRANSIT_FOR_PICKUP (to Vulcan for Nyota)
    api_checkin(librarian_page, base_url, BARCODE, LOCATIONS["starfleet"])
    api_wait_for_item_status(librarian_page, base_url, BARCODE, "in_transit")

    # CHECKIN_4.2 — Librarian checks in at Starfleet again (transit, pickup=Vulcan≠Starfleet)
    # → item stays in transit (no action per CHECKIN_4.2)
    api_checkin(librarian_page, base_url, BARCODE, LOCATIONS["starfleet"])
    api_wait_for_item_status(librarian_page, base_url, BARCODE, "in_transit")

    # ADD_REQUEST_4.1 — Nyota tries to request again → denied (already has active request)
    status = _try_request(librarian_page, base_url, item_pid, PATRONS["nyota"]["barcode"], LOCATIONS["vulcan"])
    assert status >= 400, f"Expected request to be denied, got {status}"

    # ADD_REQUEST_4.2 — James requests item, pickup at Starfleet → PENDING (different patron)
    status = _try_request(librarian_page, base_url, item_pid, PATRONS["james"]["barcode"], LOCATIONS["starfleet"])
    assert status < 400, f"James's request should succeed, got {status}"

    # CHECKOUT_4.2 — Someone tries checkout for James → denied (first pending is Nyota)
    status = _try_checkout(librarian_page, base_url, BARCODE, PATRONS["james"]["barcode"], LOCATIONS["vulcan"])
    assert status >= 400, f"Expected checkout for James to be denied, got {status}"

    # CHECKOUT_4.1 — Nyota checks out at Vulcan (patron = first pending) → ITEM_ON_LOAN
    api_checkin(librarian_page, base_url, BARCODE, LOCATIONS["vulcan"])  # receive at Vulcan first
    api_wait_for_item_status(librarian_page, base_url, BARCODE, "at_desk")
    api_checkout(librarian_page, base_url, BARCODE, PATRONS["nyota"]["barcode"], LOCATIONS["vulcan"])
    api_wait_for_item_status(librarian_page, base_url, BARCODE, "on_loan")

    # ADD_REQUEST_3.2.2.1 — James tries to request again → denied (already has PENDING)
    status = _try_request(librarian_page, base_url, item_pid, PATRONS["james"]["barcode"], LOCATIONS["starfleet"])
    assert status >= 400, f"Expected second request from James to be denied, got {status}"

    # CHECKIN_3.2.2.1 — Nyota returns at Vulcan; James pickup=Starfleet=item_lib, trans=Vulcan
    # → IN_TRANSIT_FOR_PICKUP (auto-validate James's PENDING loan)
    api_checkin(librarian_page, base_url, BARCODE, LOCATIONS["vulcan"])
    api_wait_for_item_status(librarian_page, base_url, BARCODE, "in_transit")

    # CHANGE_PICKUP_LOCATION_4 — James changes pickup to Vulcan
    _update_pickup_location(librarian_page, base_url, BARCODE, LOCATIONS["vulcan"])

    # CANCEL_REQUEST_4.1.1 — James cancels his request; no other pending → IN_TRANSIT_TO_HOUSE
    api_cancel_loan(librarian_page, base_url, BARCODE, LOCATIONS["starfleet"])
    # Item should now be heading back to home library (Starfleet)

    # CHECKOUT_5.1 — Nyota finds item at Vulcan and borrows it (still in transit)
    # For test simplicity: receive at Starfleet first, then checkout
    api_checkin(librarian_page, base_url, BARCODE, LOCATIONS["starfleet"])
    api_wait_for_item_status(librarian_page, base_url, BARCODE, "on_shelf")
    api_checkout(librarian_page, base_url, BARCODE, PATRONS["nyota"]["barcode"], LOCATIONS["starfleet"])
    api_wait_for_item_status(librarian_page, base_url, BARCODE, "on_loan")

    # CHECKIN_3.1.1 — Nyota returns at Starfleet (item_lib=Starfleet=trans_lib) → on shelf
    api_checkin(librarian_page, base_url, BARCODE, LOCATIONS["starfleet"])
    api_wait_for_item_status(librarian_page, base_url, BARCODE, "on_shelf")
