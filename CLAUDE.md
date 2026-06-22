<!--
SPDX-FileCopyrightText: Fondation RERO+
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# RERO ILS Claude guide

## Overview

rero-ils is the Python/Flask backend of the RERO ILS Integrated Library System (ILS). Some frontend elements are defined in this project as HTML/Jinja templates, the rest is a separate Angular project (rero-ils-ui) based on (ng-core).

**Stack**: Python 3.14, Flask (Invenio), PostgreSQL, Elasticsearch 7, Celery, RabbitMQ, Redis
**Package manager**: `uv` with `poethepoet` for task running

## Commands

During development, all commands are run through uv's virtual env with `uv run`.

### Linting and formatting

**IMPORTANT:** After editing files, make sure that there are no errors in the formatting and linting.

```bash
uv run poe lint     # ruff check rero_ils tests
uv run poe format   # ruff format rero_ils tests
```

### Setup (done by humans)

Human developers will run the required containers, the app setup and the servers on their own terms.

## Architecture

### Module Structure

All business logic lives in `rero_ils/modules/`. Each module follows a consistent pattern:

```text
rero_ils/modules/<module_name>/
├── api.py            # Record class + Search class (core business logic)
├── models.py         # SQLAlchemy model + Identifier + Metadata
├── views.py          # Flask blueprint (UI routes)
├── api_views.py      # Flask blueprint (REST API routes)
├── tasks.py          # Celery async tasks
├── listener.py       # Signal handlers (enrich data before indexing)
├── permissions.py    # Access control rules
├── jsonschemas/      # JSON Schema for validation
├── mappings/v7/      # Elasticsearch index mappings
├── serializers/      # REST response serializers
├── dumpers.py        # Data dumpers for ES indexing
└── jsonresolver.py   # JSON $ref resolver
```

### Base Classes

- **`IlsRecord`** (`rero_ils/modules/api.py`): extends `invenio_records.api.Record`. All domain records (Document, Item, Patron, Loan, etc.) inherit from this. Provides PID management, extended validation, and bulk indexing.
- **`IlsRecordsSearch`** (`rero_ils/modules/api.py`): extends `invenio_search.api.RecordsSearch`. Each module defines its own search class with a specific ES index.

### Signal/Event Flow

The `ext.py` file wires up all signal listeners. Before a record is indexed in Elasticsearch, `listener.py` in each module can enrich the data (e.g., adding computed fields, resolving references). This is the primary mechanism for denormalizing data into ES.

### API Entry Points

REST endpoints are registered in `pyproject.toml` under `[project.entry-points."invenio_base.api_blueprints"]`. Each module's `api_views.py` exports an `api_blueprint`.

### Permissions

Each module has a `permissions.py` using `invenio-records-permissions`. Access is typically scoped by organisation membership (multi-tenancy).

## Code Style

- Be clear and concise in the docstrings and do not over-comment the code.
- Do not use Python type annotations (no `-> str`, `: str`, etc. in signatures).

### Commit Messages

Commit messages follow [Conventional Commits](https://www.conventionalcommits.org).

Format: `<type>(<scope>): <subject>`

Rules:
- The subject line must not exceed 50 characters.
- Body lines must not exceed 72 characters.
- Use `*` for bullet points in the body, not `-`.
- Use the imperative mood in the subject ("add", not "adds").
- Do not end the subject line with a period.

Types: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `style`,
`perf`, `build`, `ci`

Scope corresponds to the affected module under `rero_ils/modules/`
(e.g. `patrons`, `items`, `loans`, `documents`).

### Translations

Translations are only added manually before a release. During standard development, only make sure that any strings that must be displayed to the end-user are marked for translations in the code, but do not run the extractor or edit any files in `rero_ils/translations`.

## Testing Notes

- Tests use function-based style (no class-based tests).
- Tests are split into `tests/api/`, `tests/unit/`, `tests/ui/`, `tests/e2e/`, `tests/scheduler/`
- The project follows a test-driven development methodology. Each commit must be accompanied by tests that ensure that the functionality works as intended. Tests must follow DRY principles and should only test specific app behaviour and not the behaviour of external modules (e.g. invenio dependencies).
- Test fixtures (shared data) are in `tests/fixtures/` and `tests/conftest.py`
- Sample data is in `tests/data/` and `data/`
- End-to-end tests (Cypress) are skipped by default because unmaintained
- Tests marked `@pytest.mark.external` hit external services and are excluded by default

### Running the tests (done by humans)

Human developers will run the needed tests from their consoles because they need to make sure the tests run only when their testing container runs.

## Behavioral guidelines

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

### 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:

- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:

- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:

- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:

- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:

```text
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
