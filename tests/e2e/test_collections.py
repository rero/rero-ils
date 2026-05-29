# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""E2E tests: collections.

The collection editor uses formly fields in the Angular professional interface.
Confirmed IDs from the compiled Angular bundle: #search-add-button, #end_date,
#detail-edit-button, #detail-delete-button.
The delete confirmation uses a PrimeNG dialog.
"""

import time

import pytest

# Unique suffix for collection IDs — constant within a run, different across runs.
_RUN_ID = str(int(time.time()))[-6:]


def _pick_date(page, field_id, day_index=0):
    """Open a p-datepicker and click the nth non-disabled day in the current month."""
    page.locator(f"#{field_id}").locator("input").click()
    days = page.locator(".p-datepicker-panel span.p-datepicker-day:not(.p-disabled)")
    days.nth(day_index).wait_for(state="visible")
    days.nth(day_index).click()
    page.wait_for_timeout(300)


def _fill_collection_editor(page, data):
    """Fill and save the collection editor form."""
    # collection_type: PrimeNG Select — click the p-select directly
    page.locator("p-select").first.click()
    page.get_by_role("option", name=data["collection_type"]).click()
    # Dates: p-datepicker — keyboard fill doesn't propagate in WebKit; use calendar UI
    _pick_date(page, "start_date", day_index=0)  # day 1 of current month
    _pick_date(page, "end_date", day_index=27)  # day 28 (always valid)
    # Title and collection ID: plain <input> with formly-generated IDs
    page.locator("#title").fill(data["title"])
    page.locator("#collection_id").fill(data["collection_id"])
    page.locator("#editor-save-button button").click(force=True)
    page.wait_for_url("**/collections/detail/**", timeout=60000)


COURSE = {
    "collection_type": "course",
    "title": f"E2E Course {_RUN_ID}",
    "collection_id": f"E2E-CRS-{_RUN_ID}",
}

EXHIBITION = {
    "collection_type": "exhibition",
    "title": f"E2E Expo {_RUN_ID}",
    "collection_id": f"E2E-Expo-{_RUN_ID}",
}


@pytest.mark.e2e
@pytest.mark.chromium_only
@pytest.mark.xfail(
    reason="Angular PrimeNG save buttons do not respond to synthetic clicks on cold CI runners; "
    "requires rero-ils-ui fix — see tests/e2e/README.md",
    strict=False,
)
def test_create_and_edit_collection(librarian_page, base_url):
    """Librarian can create a course collection then edit it as an exhibition."""
    page = librarian_page

    # ── Navigate to collections list ──────────────────────────────────────────
    page.goto(f"{base_url}/professional/records/collections/", wait_until="domcontentloaded")
    page.locator("#search-add-button").wait_for()
    page.locator("#search-add-button").click()

    # ── Create course ─────────────────────────────────────────────────────────
    _fill_collection_editor(page, COURSE)
    # Wait for Angular detail view to finish rendering before checking title
    page.locator("#detail-edit-button").wait_for(timeout=15000)
    assert COURSE["title"] in page.locator("body").inner_text()

    # ── Edit to exhibition ────────────────────────────────────────────────────
    page.locator("#detail-edit-button").click()
    _fill_collection_editor(page, EXHIBITION)
    page.locator("#detail-edit-button").wait_for(timeout=15000)
    assert EXHIBITION["title"] in page.locator("body").inner_text()

    # ── Delete the collection ─────────────────────────────────────────────────
    page.locator("#detail-delete-button").wait_for()
    page.locator("#detail-delete-button button").click(force=True)
    # Confirm in PrimeNG dialog
    dialog = page.get_by_role("dialog")
    dialog.wait_for(state="visible")
    dialog.get_by_role("button", name="Yes").click(force=True)
