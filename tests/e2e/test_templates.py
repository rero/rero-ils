# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""E2E tests: document templates.

The professional interface uses PrimeNG components:
- Save-as-template opens a PrimeNG DynamicDialog (not Bootstrap modal).
- Load-template dropdown is a PrimeNG Dropdown, not a native <select>.
"""

import time

import pytest

# Unique suffix — constant within a run, different across runs.
_RUN_ID = str(int(time.time()))[-6:]

TEMPLATE_TITLE = "E2E template title"
TEMPLATE_NAME = f"E2E Playwright template {_RUN_ID}"


@pytest.mark.e2e
@pytest.mark.chromium_only
@pytest.mark.xfail(
    reason="Angular PrimeNG save buttons do not respond to synthetic clicks on cold CI runners; "
    "requires rero-ils-ui fix — see tests/e2e/README.md",
    strict=False,
)
def test_create_and_use_template(librarian_page, base_url):
    """Librarian can save a document as a template and reload it in the editor."""
    page = librarian_page

    # ── Open document editor ──────────────────────────────────────────────────
    page.goto(f"{base_url}/professional/records/documents/new", wait_until="domcontentloaded")
    page.locator("#title-0-mainTitle-0-value").wait_for()
    page.locator("#title-0-mainTitle-0-value").fill(TEMPLATE_TITLE)

    # ── Open the split-button dropdown and click "Save as template" ───────────
    # The PrimeNG SplitButton has a caret button that opens the dropdown menu.
    split_btn = page.locator("#editor-save-button-split")
    split_btn.wait_for()
    # Click the caret (second button inside the split button)
    split_btn.locator("button.p-splitbutton-dropdown").click(force=True)
    page.get_by_text("Save as template").wait_for(state="visible")
    page.get_by_text("Save as template").click()

    # ── Fill the PrimeNG DynamicDialog ───────────────────────────────────────
    dialog = page.get_by_role("dialog")
    dialog.wait_for(state="visible")
    # Name input — PrimeNG dialog, formControlName="name" → no #id, use input inside dialog
    dialog.locator("input").fill(TEMPLATE_NAME)
    dialog.get_by_role("button", name="Save").click()
    page.wait_for_url("**/records/templates/detail/**", timeout=60000)
    assert "records/templates/detail" in page.url

    # ── Load template in a fresh editor session ───────────────────────────────
    page.goto(f"{base_url}/professional/records/documents/new", wait_until="domcontentloaded")
    page.locator("#editor-load-template-button").wait_for()
    page.locator("#editor-load-template-button").click()

    # Select template from PrimeNG Dropdown inside the dialog
    dialog = page.get_by_role("dialog")
    dialog.wait_for(state="visible")
    # Open the PrimeNG dropdown
    dialog.locator("p-dropdown").click()
    # Wait for the dropdown panel and click the template by name
    page.get_by_role("option", name=TEMPLATE_NAME).click()
    dialog.get_by_role("button", name="Load").click()

    assert page.locator("#title-0-mainTitle-0-value").input_value() == TEMPLATE_TITLE

    # ── Cleanup ───────────────────────────────────────────────────────────────
    resp = page.request.get(f"{base_url}/api/templates/", params={"q": f'name:"{TEMPLATE_NAME}"'})
    pids = [h["metadata"]["pid"] for h in resp.json().get("hits", {}).get("hits", [])]
    for pid in pids:
        page.request.delete(f"{base_url}/api/templates/{pid}")
