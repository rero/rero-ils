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

This loads: organisations, libraries, locations, item types, patron types,
circulation policies, and users. It skips documents, items, holdings,
acquisitions, statistics, wiki, and migration data.

The full setup (`uv run poe setup`) also works but takes ~15 minutes.

Playwright browsers are installed by `scripts/bootstrap`:

```bash
uv run playwright install chromium firefox webkit
```

Or manually if needed:

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

## Test structure

| File | Scenario | Browser |
| --- | --- | --- |
| `test_login.py` | Login/logout for librarian and patron | all |
| `test_circulation_scenario_a.py` | Standard loan at owning library | all |
| `test_circulation_scenario_b.py` | Standard loan with inter-library transit | all |
| `test_circulation_scenario_c.py` | Multiple requests with transit | all |
| `test_circulation_scenario_d.py` | Denied actions and unconventional workflow | all |
| `test_circulation_scenario_e.py` | Complex workflow with mid-cycle cancellations | all |
| `test_document_editor.py` | Create document via Angular editor | Chromium only |
| `test_collections.py` | Create/edit/delete collections | Chromium only |
| `test_templates.py` | Save document as template and reload it | Chromium only |

Scenarios A–E map directly to the flows described in
[`doc/circulation/scenarios.md`](../../doc/circulation/scenarios.md).

## Running in GitHub Actions

The workflow is defined in
[`.github/workflows/e2e.yml`](../../.github/workflows/e2e.yml). It runs on
every **push to master**, every **pull request**, and on a manual trigger
(`workflow_dispatch`).

### Concurrency and cancellation

The workflow uses a concurrency group keyed on `workflow + ref`:

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

This means: if a new push arrives on the same branch while a run is already
in progress, the old run is cancelled automatically. No queuing — only the
latest commit is tested.

### What the job does

1. Start Docker services (`docker compose up -d`)
2. Bootstrap Python + Node dependencies
3. Install Playwright system packages and the Chromium binary
4. Load the small fixture data set (`uv run poe setup`)
5. Start the Flask server in the background (using the test TLS certificate)
6. Run all browsers sequentially (Chromium → Firefox → WebKit)

| Step | Tests | Approximate time |
| --- | --- | --- |
| Chromium | all 9 (including `chromium_only`) | ~12 min |
| Firefox | 5 cross-browser | ~6 min |
| WebKit | 5 cross-browser | ~6 min |

Total wall-clock time ≈ **setup (5 min) + tests (24 min) = ~29 minutes**.

### Manual trigger

```bash
gh workflow run e2e.yml
```

### Further speedup with pytest-xdist (optional)

Each test file uses a unique barcode (`e2e-scenario-a`, `e2e-scenario-b`, …)
so the files are independent. Adding `pytest-xdist` to `dev` dependencies
would allow running all files in parallel within the same job:

```bash
uv run pytest tests/e2e -m e2e --browser chromium \
  --numprocesses=4 --dist=loadfile \
  -o "addopts=--color=yes"
```

`--dist=loadfile` keeps all tests in a file on the same worker, which is
required because the `autouse` fixture creates and deletes items with a
per-file barcode. This would cut the test phase from ~12 min to ~4 min.

## The `chromium_only` marker

Three test files are marked `@pytest.mark.chromium_only`. They are excluded from
the Firefox and WebKit runs and only execute under Chromium.

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
synthetic click events through Angular's zone-patched event system. There are
three places where a fix could land:

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

#### 3. `rero-ils` (this project — test-only)

Without upstream changes, the tests could use `page.evaluate(...)` to call
Angular component methods directly via the `__ngContext__` reference on DOM
elements. This approach is fragile (depends on Angular internals) but would
work for Chromium, Firefox, and WebKit:

```python
# Trigger save via Angular component context (Chromium/Firefox/WebKit)
page.evaluate("""() => {
    const btn = document.querySelector('#editor-save-button button');
    const zone = window.Zone?.current;
    if (zone) zone.run(() => btn.dispatchEvent(
        new MouseEvent('click', {bubbles: true, composed: true})
    ));
}""")
```

In practice this was tried and did not work, because the Angular 19 + PrimeNG
event pipeline does not respond to synthetic events dispatched outside its own
change-detection cycle regardless of Zone wrapping. A structural change in
`rero-ils-ui` or `ng-core` is the recommended path.
