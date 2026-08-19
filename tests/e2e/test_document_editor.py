# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""E2E tests: document editor."""

import pytest

from .conftest import api_delete


def _open_editor(page, base_url, title):
    """Navigate to the new document editor and fill the title."""
    page.goto(f"{base_url}/professional/records/documents/new", wait_until="domcontentloaded")
    # Wait for the title field — this confirms formly has rendered the form
    page.locator("#title-0-mainTitle-0-value").wait_for()
    page.locator("#title-0-mainTitle-0-value").fill(title)
    # Provision activity date — required in WebKit/CI (formly fills it in local Chromium)
    page.locator("#provisionActivity-0-startDate").fill("2024")


def _save_and_wait(page):
    """Click the split-button Save action and return the new document PID."""
    save_btn = page.locator("#editor-save-button-split button.p-splitbutton-button")
    save_btn.wait_for(state="visible")
    save_btn.click(force=True)
    page.wait_for_url("**/documents/detail/**", timeout=60000)
    return page.url.rstrip("/").split("/")[-1]


@pytest.mark.e2e
@pytest.mark.chromium_only
@pytest.mark.xfail(
    reason="Angular PrimeNG save buttons do not respond to synthetic clicks on cold CI runners; "
    "requires rero-ils-ui fix — see tests/e2e/README.md",
    strict=False,
)
def test_create_simple_document(librarian_page, base_url):
    """Librarian can create a document with essential fields via the Angular editor."""
    page = librarian_page
    title = "E2E test document simple"

    _open_editor(page, base_url, title)
    doc_pid = _save_and_wait(page)

    assert title in page.locator("body").inner_text()
    api_delete(page, base_url, "documents", doc_pid)


@pytest.mark.e2e
@pytest.mark.chromium_only
@pytest.mark.xfail(
    reason="Angular PrimeNG save buttons do not respond to synthetic clicks on cold CI runners; "
    "requires rero-ils-ui fix — see tests/e2e/README.md",
    strict=False,
)
def test_create_document_saves_via_api(librarian_page, base_url):
    """Document created via editor is retrievable via the REST API."""
    page = librarian_page
    title = "E2E API-verifiable document"

    _open_editor(page, base_url, title)
    doc_pid = _save_and_wait(page)

    resp = page.request.get(f"{base_url}/api/documents/{doc_pid}")
    assert resp.ok
    titles = resp.json().get("metadata", {}).get("title", [])
    assert any(entry.get("mainTitle", [{}])[0].get("value") == title for entry in titles)

    api_delete(page, base_url, "documents", doc_pid)
