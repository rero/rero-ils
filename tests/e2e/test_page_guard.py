# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""E2E tests: the console/network guard attached to every page fixture.

The guard is what makes every other test in this directory report browser-side
failures, so its three channels are verified here on a page it may break freely.
"""

import pytest

from .conftest import PageGuard, http_allowed


@pytest.fixture()
def unguarded_page(browser, base_url):
    """A page on the home page, outside the guarded fixtures, free to be broken."""
    ctx = browser.new_context(base_url=base_url, ignore_https_errors=True)
    p = ctx.new_page()
    p.goto(base_url, wait_until="domcontentloaded")
    yield p
    ctx.close()


@pytest.mark.e2e
def test_guard_catches_console_error(unguarded_page):
    """A console.error() call fails the test it happened in."""
    guard = PageGuard(unguarded_page)
    with unguarded_page.expect_console_message():
        unguarded_page.evaluate("console.error('e2e guard probe')")

    with pytest.raises(AssertionError, match="e2e guard probe"):
        guard.assert_clean()


@pytest.mark.e2e
def test_guard_catches_uncaught_exception(unguarded_page):
    """An exception reaching the top level of the page fails the test."""
    guard = PageGuard(unguarded_page)
    with unguarded_page.expect_event("pageerror"):
        unguarded_page.evaluate("setTimeout(() => { throw new Error('e2e guard boom'); })")

    with pytest.raises(AssertionError, match="e2e guard boom"):
        guard.assert_clean()


@pytest.mark.e2e
def test_guard_catches_failed_response(unguarded_page):
    """A 4xx answer to a request issued by the interface fails the test."""
    guard = PageGuard(unguarded_page)
    with unguarded_page.expect_response("**/api/e2e-guard-probe"):
        unguarded_page.evaluate("fetch('/api/e2e-guard-probe')")

    with pytest.raises(AssertionError, match="HTTP 404"):
        guard.assert_clean()


@pytest.mark.e2e
def test_guard_ignores_ordinary_console_output(unguarded_page):
    """Anything that is not console.error() leaves the guard silent."""
    unguarded_page.goto("about:blank")
    guard = PageGuard(unguarded_page)
    with unguarded_page.expect_console_message():
        unguarded_page.evaluate("console.warn('e2e guard warning')")

    guard.assert_clean()


@pytest.mark.e2e
def test_allowlist_only_covers_documented_answers(base_url):
    """A documented non-2xx answer is tolerated, a neighbouring one is not."""
    assert http_allowed("POST", f"{base_url}/api/item/checkin", 400)
    assert not http_allowed("POST", f"{base_url}/api/item/checkout", 400)
    assert not http_allowed("POST", f"{base_url}/api/item/checkin", 500)
