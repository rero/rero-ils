# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Pytest configuration and shared fixtures for Playwright E2E tests.

Run with:
    uv run pytest tests/e2e -m e2e --base-url https://localhost:5000

Requires a running RERO ILS instance loaded with the standard small
fixture data set (``uv run invenio reroils setup -s``).
"""

import contextlib
import os
import ssl
import time
import urllib.request

import pytest


@pytest.fixture(scope="session", autouse=True)
def _wait_for_server(base_url):
    """Poll /api/ping until the server is ready before any test runs."""
    url = f"{base_url}/api/ping"
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    for _ in range(30):
        with contextlib.suppress(Exception), urllib.request.urlopen(url, context=ctx, timeout=2) as resp:
            if b"OK" in resp.read():
                return
        time.sleep(2)
    pytest.fail(f"Server at {base_url} did not become ready within 60 s")


# pytest-invenio skips any test whose fixture chain contains "browser" unless
# E2E=yes. Every pytest-playwright test uses page → browser_context → browser,
# so we set it here to avoid needing it as an external environment variable.
os.environ.setdefault("E2E", "yes")

# ── Test credentials (match the small fixture data set) ──────────────────────

PASSWORD = "Pw123456"

LIBRARIANS = {
    "leonard": {
        "email": "reroilstest+leonard@gmail.com",
        "first_name": "Leonard",
        "last_name": "McCoy",
        "patron_pid": "50",
    },
    "spock": {
        "email": "reroilstest+spock@gmail.com",
        "first_name": "Spock",
        "last_name": "Grayson",
        "patron_pid": "51",
    },
}

PATRONS = {
    "james": {
        "email": "reroilstest+james@gmail.com",
        "first_name": "James",
        "last_name": "Kirk",
        "barcode": "e2e-test-1",
    },
    "nyota": {
        "email": "reroilstest+nyota@gmail.com",
        "first_name": "Nyota",
        "last_name": "Uhura",
        "barcode": "e2e-test-2",
    },
}

# PIDs from the small fixture data set
LOCATIONS = {"starfleet": 35, "vulcan": 36}
LIBRARIES = {"starfleet": 22, "vulcan": 23}
ITEM_TYPES = {"default": 11}


# ── Browser configuration ─────────────────────────────────────────────────────

_CONTEXT_ARGS = {"ignore_https_errors": True}


_DEFAULT_TIMEOUT_MS = 60000  # Angular loads slower on CI runners


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Ignore self-signed TLS certificate on localhost."""
    return {**browser_context_args, **_CONTEXT_ARGS}


@pytest.fixture()
def context(context):
    """Raise the default Playwright timeout to 60 s for all operations.

    pytest-playwright's default is 30 s which is too short for Angular on CI.
    The correct way to set a global timeout is via context.set_default_timeout().
    """
    context.set_default_timeout(_DEFAULT_TIMEOUT_MS)
    yield context


@pytest.fixture(scope="session")
def browser(browser_type, browser_type_launch_args):
    """Override pytest-invenio's Selenium browser fixture with a Playwright browser.

    pytest-invenio registers a session-scoped 'browser' fixture for Selenium
    WebDriver. Its pytest_generate_tests hook parametrises any test whose fixture
    chain contains 'browser' (including the page→browser_context→browser chain
    used by pytest-playwright). By shadowing the fixture here we ensure the
    resolved browser is a Playwright Browser, so both the page fixture and our
    custom per-test fixtures work correctly. The [Chrome] parametrisation label
    from pytest-invenio is harmless.
    """
    pw_browser = browser_type.launch(**browser_type_launch_args)
    yield pw_browser
    pw_browser.close()


def _make_page(pw_browser, base_url, email, start_url=None):
    """Create an isolated browser context + page logged in as the given user.

    Takes a playwright Browser instance (not pytest-invenio's Selenium browser).
    """
    ctx = pw_browser.new_context(base_url=base_url, **_CONTEXT_ARGS)
    ctx.set_default_timeout(_DEFAULT_TIMEOUT_MS)
    p = ctx.new_page()
    resp = p.request.post(f"{base_url}/api/login", data={"email": email, "password": PASSWORD})
    assert resp.ok, f"Login failed for {email!r}: {resp.status} {resp.text()}"
    p.goto(f"{base_url}/lang/en", wait_until="domcontentloaded")
    if start_url:
        p.goto(start_url, wait_until="domcontentloaded")
    return p, ctx


# ── Login helpers ─────────────────────────────────────────────────────────────


def login(page, email, base_url):
    """Log in via the REST API and navigate to the English-language UI."""
    resp = page.request.post(
        f"{base_url}/api/login",
        data={"email": email, "password": PASSWORD},
    )
    assert resp.ok, f"Login failed for {email!r}: {resp.status} {resp.text()}"
    page.goto(f"{base_url}/lang/en", wait_until="domcontentloaded")


def logout(page, base_url):
    """Log out and wait for the public page to load."""
    page.goto(f"{base_url}/signout/", wait_until="domcontentloaded")


@pytest.fixture()
def librarian_page(browser, base_url):
    """Isolated context + page logged in as Leonard at the professional UI."""
    p, ctx = _make_page(browser, base_url, LIBRARIANS["leonard"]["email"], f"{base_url}/professional")
    yield p
    ctx.close()


@pytest.fixture()
def spock_page(browser, base_url):
    """Isolated context + page logged in as Spock (Vulcan library)."""
    p, ctx = _make_page(browser, base_url, LIBRARIANS["spock"]["email"], f"{base_url}/professional")
    yield p
    ctx.close()


@pytest.fixture()
def patron_page(browser, base_url):
    """Isolated context + page logged in as patron James."""
    p, ctx = _make_page(browser, base_url, PATRONS["james"]["email"])
    yield p
    ctx.close()


# ── API helpers ───────────────────────────────────────────────────────────────


def api_create_document(page, base_url, title_suffix=""):
    """Create a minimal test document via the REST API and return its PID."""
    resp = page.request.post(
        f"{base_url}/api/documents/",
        data={
            "type": [{"main_type": "docmaintype_book", "subtype": "docsubtype_other_book"}],
            "title": [{"type": "bf:Title", "mainTitle": [{"value": f"E2E test document{title_suffix}"}]}],
            "language": [{"type": "bf:Language", "value": "fre"}],
            "provisionActivity": [
                {
                    "type": "bf:Publication",
                    "startDate": 2020,
                    "statement": [
                        {"type": "bf:Place", "label": [{"value": "Place"}]},
                        {"type": "bf:Agent", "label": [{"value": "Agent"}]},
                        {"type": "Date", "label": [{"value": "2020"}]},
                    ],
                    "place": [{"country": "xx"}],
                }
            ],
            "issuance": {"main_type": "rdami:1001", "subtype": "materialUnit"},
            "fiction_statement": "unspecified",
            "adminMetadata": {"encodingLevel": "Not applicable"},
        },
    )
    assert resp.ok
    return resp.json()["id"]


def api_create_item(
    page,
    base_url,
    document_pid,
    barcode,
    location_pid=35,
    item_type_pid=11,
):
    """Create a test item via the REST API and return its PID.

    If an item with the same barcode already exists (from a failed previous run),
    returns its PID without creating a duplicate.
    """
    existing = page.request.get(f"{base_url}/api/items/", params={"q": f'barcode:"{barcode}"'})
    if hits := existing.json().get("hits", {}).get("hits", []):
        return hits[0]["metadata"]["pid"]

    resp = page.request.post(
        f"{base_url}/api/items/",
        data={
            "type": "standard",
            "status": "on_shelf",
            "barcode": barcode,
            "call_number": barcode,
            "document": {"$ref": f"https://bib.rero.ch/api/documents/{document_pid}"},
            "location": {"$ref": f"https://bib.rero.ch/api/locations/{location_pid}"},
            "item_type": {"$ref": f"https://bib.rero.ch/api/item_types/{item_type_pid}"},
        },
    )
    assert resp.ok
    return resp.json()["id"]


def api_delete(page, base_url, resource, pid):
    """Delete a single resource record."""
    page.request.delete(f"{base_url}/api/{resource}/{pid}")


def api_validate_request(page, base_url, item_pid):
    """Validate a pending item request via REST API (librarian page must be logged in).

    No-op if no PENDING loan exists (already validated in a previous run).
    """
    loans_resp = page.request.get(
        f"{base_url}/api/loans/",
        params={"q": f"item_pid.value:{item_pid} AND state:PENDING"},
    )
    hits = loans_resp.json()["hits"]["hits"]
    if not hits:
        return  # already validated or no pending request
    loan_pid = hits[0]["metadata"]["pid"]
    lib_pid = LIBRARIANS["leonard"]["patron_pid"]
    barcode = page.request.get(f"{base_url}/api/items/{item_pid}").json()["metadata"]["barcode"]
    # Use the item's actual location as transaction location for correct transit calculation
    item_data = page.request.get(f"{base_url}/api/items/{item_pid}").json()["metadata"]
    item_location_pid = item_data["location"]["$ref"].split("/")[-1]
    page.request.post(
        f"{base_url}/api/item/validate_request",
        data={
            "item_barcode": barcode,
            "pid": loan_pid,
            "transaction_location_pid": item_location_pid,
            "transaction_user_pid": lib_pid,
        },
    )


def api_request_item(page, base_url, item_pid, pickup_location_pid=35):
    """Create a patron loan request via REST API.

    The logged-in page must be the LIBRARIAN (Leonard) who requests on behalf of patron James.
    """
    # Look up patron James's pid
    patron_resp = page.request.get(
        f"{base_url}/api/patrons/",
        params={"q": f'barcode:"{PATRONS["james"]["barcode"]}"'},
    )
    patron_pid = patron_resp.json()["hits"]["hits"][0]["metadata"]["pid"]

    resp = page.request.post(
        f"{base_url}/api/item/request",
        data={
            "item_pid": item_pid,
            "pickup_location_pid": str(pickup_location_pid),
            "patron_pid": patron_pid,
            "transaction_library_pid": str(LIBRARIES["starfleet"]),
            "transaction_user_pid": LIBRARIANS["leonard"]["patron_pid"],
        },
    )
    # 403 = already has an active request; skip silently
    assert resp.ok or resp.status == 403, f"api_request_item failed: {resp.status} {resp.json()}"


def api_get_patron_pid(page, base_url, barcode):
    """Return the patron PID for a given patron barcode."""
    resp = page.request.get(f"{base_url}/api/patrons/", params={"q": f'barcode:"{barcode}"'})
    return resp.json()["hits"]["hits"][0]["metadata"]["pid"]


def api_request_for_patron(
    page,
    base_url,
    item_pid,
    patron_barcode,
    pickup_location_pid,
    transaction_location_pid=LOCATIONS["starfleet"],
):
    """Create an item request for a specific patron via REST API."""
    patron_pid = api_get_patron_pid(page, base_url, patron_barcode)
    resp = page.request.post(
        f"{base_url}/api/item/request",
        data={
            "item_pid": item_pid,
            "pickup_location_pid": str(pickup_location_pid),
            "patron_pid": patron_pid,
            "transaction_location_pid": str(transaction_location_pid),
            "transaction_user_pid": LIBRARIANS["leonard"]["patron_pid"],
        },
    )
    assert resp.ok or resp.status == 403, f"api_request_for_patron failed: {resp.status} {resp.json()}"


def api_checkout(
    page,
    base_url,
    item_barcode,
    patron_barcode,
    transaction_location_pid,
):
    """Checkout an item to a patron via REST API."""
    patron_pid = api_get_patron_pid(page, base_url, patron_barcode)
    resp = page.request.post(
        f"{base_url}/api/item/checkout",
        data={
            "item_barcode": item_barcode,
            "patron_pid": patron_pid,
            "transaction_location_pid": str(transaction_location_pid),
            "transaction_user_pid": LIBRARIANS["leonard"]["patron_pid"],
        },
    )
    assert resp.ok, f"api_checkout failed: {resp.status} {resp.json()}"


def api_checkin(
    page,
    base_url,
    item_barcode,
    transaction_location_pid,
):
    """Checkin an item via REST API (also handles receive/house_receive).

    Returns the response JSON. Does not assert on status because some checkin
    operations are valid no-ops (400 'No circulation action performed') per the
    RERO ILS circulation state machine (e.g. CHECKIN_1.1.1, CHECKIN_4.2).
    """
    resp = page.request.post(
        f"{base_url}/api/item/checkin",
        data={
            "item_barcode": item_barcode,
            "transaction_location_pid": str(transaction_location_pid),
            "transaction_user_pid": LIBRARIANS["leonard"]["patron_pid"],
        },
    )
    return resp.json()


def api_extend_loan(
    page,
    base_url,
    item_barcode,
    transaction_location_pid,
):
    """Extend the current loan for an item via REST API.

    Returns the response JSON. Does not assert because extension can be legitimately
    denied when the renewal duration would not push the due date forward (loan just
    created, renewal_duration = checkout_duration).
    """
    resp = page.request.post(
        f"{base_url}/api/item/extend_loan",
        data={
            "item_barcode": item_barcode,
            "transaction_location_pid": str(transaction_location_pid),
            "transaction_user_pid": LIBRARIANS["leonard"]["patron_pid"],
        },
    )
    return resp.json()


def api_cancel_loan(
    page,
    base_url,
    item_barcode,
    transaction_location_pid,
):
    """Cancel the most recent active loan for an item via REST API."""
    item_resp = page.request.get(f"{base_url}/api/items/", params={"q": f'barcode:"{item_barcode}"'})
    item_pid = item_resp.json()["hits"]["hits"][0]["metadata"]["pid"]
    loans_resp = page.request.get(
        f"{base_url}/api/loans/",
        params={"q": f"item_pid.value:{item_pid} AND state:({_ACTIVE_LOAN_STATES})"},
    )
    hits = loans_resp.json().get("hits", {}).get("hits", [])
    if not hits:
        return
    loan_pid = hits[0]["metadata"]["pid"]
    page.request.post(
        f"{base_url}/api/item/cancel_item_request",
        data={
            "item_barcode": item_barcode,
            "pid": loan_pid,
            "transaction_location_pid": str(transaction_location_pid),
            "transaction_user_pid": LIBRARIANS["leonard"]["patron_pid"],
        },
    )


_ACTIVE_LOAN_STATES = (
    "PENDING OR ITEM_AT_WAREHOUSE OR ITEM_IN_TRANSIT_FOR_PICKUP"
    " OR ITEM_ON_LOAN OR ITEM_IN_TRANSIT_TO_HOUSE OR ITEM_AT_DESK"
)


_CHECKOUT_STATES = {"ITEM_ON_LOAN", "ITEM_IN_TRANSIT_TO_HOUSE"}


def api_cleanup_items_by_barcode(page, base_url, barcode):
    """Delete any existing items with the given barcode, resolving active loans first.

    ITEM_ON_LOAN / ITEM_IN_TRANSIT_TO_HOUSE require a checkin (not cancel_item_request).
    All other active states use cancel_item_request.
    """
    lib_pid = LIBRARIANS["leonard"]["patron_pid"]
    resp = page.request.get(f"{base_url}/api/items/", params={"q": f'barcode:"{barcode}"'})
    for hit in resp.json().get("hits", {}).get("hits", []):
        item_pid = hit["metadata"]["pid"]
        loans_resp = page.request.get(
            f"{base_url}/api/loans/",
            params={"q": f"item_pid.value:{item_pid} AND state:({_ACTIVE_LOAN_STATES})"},
        )
        for loan in loans_resp.json().get("hits", {}).get("hits", []):
            loan_pid = loan["metadata"]["pid"]
            if loan["metadata"]["state"] in _CHECKOUT_STATES:
                # Return the item to its home location via checkin
                page.request.post(
                    f"{base_url}/api/item/checkin",
                    data={
                        "item_barcode": barcode,
                        "transaction_location_pid": str(LOCATIONS["starfleet"]),
                        "transaction_user_pid": lib_pid,
                    },
                )
                # If still in transit after first checkin, receive at home
                page.request.post(
                    f"{base_url}/api/item/checkin",
                    data={
                        "item_barcode": barcode,
                        "transaction_location_pid": str(LOCATIONS["starfleet"]),
                        "transaction_user_pid": lib_pid,
                    },
                )
            else:
                page.request.post(
                    f"{base_url}/api/item/cancel_item_request",
                    data={
                        "item_barcode": barcode,
                        "pid": loan_pid,
                        "transaction_location_pid": str(LOCATIONS["starfleet"]),
                        "transaction_user_pid": lib_pid,
                    },
                )
        api_delete(page, base_url, "items", item_pid)


def wait_for_item_indexed(page, base_url, barcode, timeout_ms=15000):
    """Poll ES until the item and its holding appear in the search indexes."""
    for _ in range(timeout_ms // 500):
        item_resp = page.request.get(f"{base_url}/api/items/", params={"q": f'barcode:"{barcode}"'})
        if hits := item_resp.json().get("hits", {}).get("hits", []):
            if doc_pid := hits[0]["metadata"].get("document", {}).get("pid"):
                holding_resp = page.request.get(
                    f"{base_url}/api/holdings/",
                    params={"q": f"document.pid:{doc_pid}"},
                )
                if holding_resp.json().get("hits", {}).get("total", {}).get("value", 0) > 0:
                    return
        page.wait_for_timeout(500)
    raise TimeoutError(f"Item/holding for barcode {barcode!r} not indexed after {timeout_ms}ms")


# ── Navigation / circulation helpers ─────────────────────────────────────────


CIRCULATION_PLACEHOLDER = "Please enter a patron card number or an item barcode."
CIRCULATION_ITEM_PLACEHOLDER = "Checkout/check-in: please enter an item barcode."
REQUESTS_PLACEHOLDER = "Please enter an item barcode."


def go_to_circulation(page, base_url):
    """Navigate to the Angular circulation checkout/checkin view."""
    page.goto(f"{base_url}/professional/circulation", wait_until="domcontentloaded")
    page.get_by_placeholder(CIRCULATION_PLACEHOLDER).wait_for()


def scan_barcode(page, barcode):
    """Type a barcode in the circulation search input and press Enter."""
    inp = page.get_by_placeholder(CIRCULATION_PLACEHOLDER)
    inp.fill(barcode)
    inp.press("Enter")


def scan_patron_then_item(page, patron_barcode, item_barcode):
    """Scan patron barcode (checkout start), then item barcode (checkout).

    After scanning the patron, the placeholder changes to the item-only variant.
    """
    scan_barcode(page, patron_barcode)
    page.locator("#patron-last-name").wait_for()
    # After patron is scanned, the input placeholder changes
    inp = page.get_by_placeholder(CIRCULATION_ITEM_PLACEHOLDER)
    inp.fill(item_barcode)
    inp.press("Enter")


def api_get_item_status(page, base_url, barcode):
    """Return the current status of an item by barcode via REST API."""
    resp = page.request.get(f"{base_url}/api/items/", params={"q": f'barcode:"{barcode}"'})
    hits = resp.json().get("hits", {}).get("hits", [])
    return hits[0]["metadata"]["status"] if hits else ""


def api_wait_for_item_status(page, base_url, barcode, expected, timeout_ms=15000):
    """Poll ES until the item reaches the expected status.

    The UI action may complete before Elasticsearch finishes reindexing,
    so asserting directly on api_get_item_status can return stale data.
    This helper retries until the expected status appears or the timeout is
    exceeded, at which point it raises AssertionError with the last seen value.
    """
    for _ in range(timeout_ms // 500):
        status = api_get_item_status(page, base_url, barcode)
        if status == expected:
            return
        page.wait_for_timeout(500)
    status = api_get_item_status(page, base_url, barcode)
    assert status == expected, f"Item {barcode!r} status: expected {expected!r}, got {status!r}"
