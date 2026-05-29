# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""E2E tests: login and logout flows."""

import pytest

from .conftest import LIBRARIANS, PATRONS, login, logout


@pytest.mark.e2e
def test_librarian_login(page, base_url):
    """Librarian can log in, see their name in the account menu, and access the professional UI."""
    login(page, LIBRARIANS["leonard"]["email"], base_url)

    # Name in account menu — format is "LastName, FirstName"
    name = f"{LIBRARIANS['leonard']['last_name']}, {LIBRARIANS['leonard']['first_name']}"
    page.locator("#my-account-menu").first.wait_for()
    assert name in page.locator("#my-account-menu").first.inner_text()

    # Professional interface is a pure Angular SPA — verify we can reach it (not redirected to login)
    page.goto(f"{base_url}/professional", wait_until="domcontentloaded")
    page.wait_for_selector("admin-root")
    assert "/professional" in page.url

    logout(page, base_url)


@pytest.mark.e2e
def test_logout(page, base_url):
    """After logout the account menu shows 'My account' again."""
    login(page, LIBRARIANS["leonard"]["email"], base_url)
    page.locator("#my-account-menu").first.wait_for()

    logout(page, base_url)

    page.locator("#my-account-menu").first.wait_for()
    assert "my account" in page.locator("#my-account-menu").first.inner_text().lower()


@pytest.mark.e2e
def test_patron_login(page, base_url):
    """Patron can log in and sees their name in the account menu."""
    login(page, PATRONS["james"]["email"], base_url)

    name = f"{PATRONS['james']['last_name']}, {PATRONS['james']['first_name']}"
    page.locator("#my-account-menu").first.wait_for()
    assert name in page.locator("#my-account-menu").first.inner_text()

    logout(page, base_url)
