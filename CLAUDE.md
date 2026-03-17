# RERO ILS Claude guide

## Overview

rero-ils is the Python/Flask backend of the RERO ILS Integrated Library System (ILS). Some frontend elements are defined in this project as HTML/Jinja templates, the rest is a separate Angular project (rero-ils-ui) based on (ng-core).

**Stack**: Python 3.12, Flask (Invenio), PostgreSQL, Elasticsearch 7, Celery, RabbitMQ, Redis
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
- Commit messages follow [Conventional Commits](https://www.conventionalcommits.org)

### Translations

Translations are only added manually before a release. During standard development, only make sure that any strings that must be displayed to the end-user are marked for translations in the code, but do not run the extractor or edit any files in `rero_ils/translations`.

## Testing Notes

- Tests are split into `tests/api/`, `tests/unit/`, `tests/ui/`, `tests/e2e/`, `tests/scheduler/`
- The project follows a test-driven development methodology. Each commit must be accompanied by tests that ensure that the functionality works as intended. Tests must follow DRY principles and should only test specific app behaviour and not the behaviour of external modules (e.g. invenio dependencies).
- Test fixtures (shared data) are in `tests/fixtures/` and `tests/conftest.py`
- Sample data is in `tests/data/` and `data/`
- End-to-end tests (Cypress) are skipped by default because unmaintained
- Tests marked `@pytest.mark.external` hit external services and are excluded by default

### Running the tests (done by humans)

Human developers will run the needed tests from their consoles because they need to make sure the tests run only when their testing container runs.
