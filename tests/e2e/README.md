<!--
SPDX-FileCopyrightText: Fondation RERO+
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# E2E Tests

Playwright-based end-to-end tests for RERO ILS. Tests run against a live server
instance and exercise the full application stack including Angular, Flask, and
the REST API.

## Prerequisites

A running RERO ILS stack (PostgreSQL, Elasticsearch, Redis, RabbitMQ, the Flask
dev server) loaded with the **minimal E2E fixture set**:

```bash
uv run poe setup_e2e   # ~3-5 min — loads only what the tests need
```

It loads only the configuration records and users the tests need, without
documents, items or holdings.

The full setup (`uv run poe setup`) also works but takes ~15 minutes.

Playwright browsers are installed by `scripts/bootstrap`, or manually with:

```bash
uv run playwright install chromium firefox webkit
```

## Running the tests

| Command | Browsers | Tests included |
| --- | --- | --- |
| `uv run poe e2e` | Chromium + Firefox + WebKit | cross-browser tests only |
| `uv run poe e2e_chromium` | Chromium | **all** tests (including `chromium_only`) |
| `uv run poe e2e_firefox` | Firefox | cross-browser tests only |
| `uv run poe e2e_webkit` | WebKit | cross-browser tests only |

The `uv run poe e2e*` tasks already include `--base-url https://localhost:5000`.
To run against a different server, call `pytest` directly:

```bash
uv run pytest tests/e2e -m e2e --base-url https://my-server:5000 --browser chromium \
  -o "addopts=--color=yes"
```

## Circulation scenarios

`test_circulation_scenario_a.py` to `_e.py` map directly to the flows described in
[`doc/circulation/scenarios.md`](../../doc/circulation/scenarios.md).

## The console/network guard

Every page fixture (`page`, `librarian_page`, `spock_page`, `patron_page`) is
watched by a `PageGuard` declared in `conftest.py`. It listens to three browser
channels and, once the test body is over, fails the test on anything it heard:

| Channel | Fails on |
| --- | --- |
| `console` | any `console.error()` not listed in `CONSOLE_ALLOWLIST` |
| `pageerror` | any exception reaching the top level of the page not listed in `PAGE_ERROR_ALLOWLIST` |
| `response` | any 4xx/5xx answer not listed in `HTTP_ALLOWLIST` |

A test that navigates through a view raising errors therefore fails even when
its own assertions pass.

Only requests issued **by the browser** are seen. The `api_*` helpers use
Playwright's `page.request` API, which bypasses the page, so the deliberately
denied circulation calls of scenarios D and E stay invisible to the guard.

### Allowlisting

The allowlists live at the top of the guard section in `conftest.py`.
`HTTP_ALLOWLIST` holds `(method, url substring, status)` triples for the non-2xx
answers the application returns by design. `CONSOLE_ALLOWLIST` and
`PAGE_ERROR_ALLOWLIST` hold plain substrings and must stay short: add to them
only noise that no application change can fix, with a comment saying why.

Console errors are recorded with the location Chromium reports, because its
network-level messages ("Failed to load resource: …") never name the resource
in their text.

The guard stays silent when the test has already failed on its own assertion,
so a real failure is never buried under the browser errors it caused.

## Running in GitHub Actions

The workflow is defined in
[`.github/workflows/e2e.yml`](../../.github/workflows/e2e.yml). A new push
cancels the run in progress on the same branch.

### Manual trigger

```bash
gh workflow run e2e.yml
```

## The `chromium_only` marker

Tests marked `@pytest.mark.chromium_only` are excluded from the Firefox and
WebKit runs and only execute under Chromium.

### Why the limitation exists

The affected tests interact with the **Angular professional interface**
(`/professional`) — specifically with PrimeNG form save buttons and the
PrimeNG DatePicker.

When Playwright clicks a `<button type="submit">` inside a PrimeNG `<p-button>`
component, or presses Enter in a PrimeNG DatePicker input, the Angular event
binding fires correctly in Chromium but is silently dropped in Firefox and WebKit.
Symptoms:

- `#editor-save-button button` click does not trigger the Angular `(onClick)` output → the document is never saved.
- `#editor-save-button-split button.p-splitbutton-button` same issue for the split save button.
- PrimeNG `<p-datepicker>` input ignores `fill()`, `press_sequentially()`, and `keyboard.type()` in WebKit — the calendar panel intercepts all keystrokes.

Workarounds used for the circulation tests (which **do** pass in all browsers)
avoid this problem by driving the application entirely through the REST API for
state changes, and only using the Angular UI for pure navigation and read
assertions.

### How to lift the restriction

The root cause is a gap in how Playwright's Firefox and WebKit drivers propagate
synthetic click events through Angular's zone-patched event system. Dispatching
a synthetic click from `page.evaluate()`, even inside `Zone.run()`, does not
reach the PrimeNG handlers either, so the fix has to land in one of two places:

#### 1. `rero-ils-ui` (Angular application)

Add an explicit `(click)` output handler on the inner `<button>` elements of
`p-button` and `p-splitbutton` that calls Angular's change-detection cycle.
Alternatively, replace `p-button` with a plain `<button>` in the editor toolbar,
which Playwright can click reliably in all browsers:

```html
<!-- Instead of <p-button id="editor-save-button"> -->
<button id="editor-save-button" type="submit" class="p-button p-component"
        (click)="save()">
  <span class="p-button-label">Save</span>
</button>
```

For the DatePicker, use the `showOnFocus="false"` option and rely only on the
calendar icon button to open the panel, so the text input stays focusable:

```html
<p-datepicker [showOnFocus]="false" [showIcon]="true" ...>
```

#### 2. `ng-core` (shared Angular library)

The `ng-core-search-input` component (used in the circulation checkout/checkin
view) and any other custom inputs could emit a standard `input` DOM event from
their Angular event handlers. This would ensure Playwright's synthetic events
propagate through the component's `ControlValueAccessor`.
