# Plan: Automatic Deletion of Inactive Patron Profiles

## User Story

As a system librarian managing an organisation, I want to configure a monthly automatic deletion of inactive patron profiles.

## Acceptance Criteria (from Taiga US#2802)

1. A Celery task deletes inactive patrons according to specific criteria.
2. In each organisation, delete every patron where **ALL** criteria are met:
   - `patron` in `roles` (and NO professional roles)
   - `expiration_date` < (now - X years) — configurable
   - no active fee/loan linked to this patron (`get_links_to_me`)
   - no non-anonymized historical loans
   - `patron.blocked` != true (only explicit `true` blocks deletion)
   - `patron_type` is NOT in a configurable exclusion list
   - last connection date of Invenio user < (now - X years) — configurable
3. The configurable variables are saved in each organisation resource (no edition UI needed).
4. Verify that patron deletion has no unintended consequence on stats, linked resources, etc.
5. After patron cleanup, delete orphaned Invenio user accounts (users with no remaining patron records).

---

## 1. Organisation Schema: Add Configuration Fields

### Files to modify

- `rero_ils/modules/organisations/jsonschemas/organisations/organisation-v0.0.1.json`
- `rero_ils/modules/organisations/mappings/v7/organisations/organisation-v0.0.1.json`

### Changes

Add a new optional `patron_cleanup` object to the organisation JSON schema:

```json
"patron_cleanup": {
  "title": "Patron cleanup configuration",
  "description": "Configuration for the automatic deletion of inactive patron profiles.",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "expiration_years",
    "inactivity_years"
  ],
  "properties": {
    "expiration_years": {
      "title": "Expiration threshold (years)",
      "description": "Delete patrons whose expiration_date is older than this many years ago.",
      "type": "integer",
      "minimum": 1
    },
    "inactivity_years": {
      "title": "Inactivity threshold (years)",
      "description": "Delete patrons whose user last logged in more than this many years ago.",
      "type": "integer",
      "minimum": 1
    },
    "excluded_patron_types": {
      "title": "Excluded patron types",
      "description": "List of patron type PIDs to exclude from automatic deletion.",
      "type": "array",
      "uniqueItems": true,
      "items": {
        "type": "string",
        "minLength": 1
      }
    }
  }
}
```

The ES mapping needs a corresponding `patron_cleanup` object mapping (with `keyword`/`integer`/`keyword` types). This is only for completeness since the task reads from the DB, not from ES.

### Rationale

- The field is optional: organisations without it are simply skipped by the task.
- No UI is needed (per acceptance criteria). System librarians can set the config via the REST API (`PUT /api/organisations/<pid>`).
- Using patron type PIDs (not `$ref`) keeps it simple since this is a config list, not a relational reference.

---

## 2. Wire Operation Logs on Patron Resource

Before implementing the deletion task, enable operation log tracking on patrons so that all patron CRUD operations (including deletions by the task) are audited.

### Files to modify

- `rero_ils/modules/patrons/api.py` — add extension to `_extensions` list
- `rero_ils/config.py` — add `"patrons": "ptrn"` to `RERO_ILS_ENABLE_OPERATION_LOG`

### Changes

In `rero_ils/modules/patrons/api.py`, add the `OperationLogObserverExtension` to the Patron class:

```python
from rero_ils.modules.operation_logs.extensions import OperationLogObserverExtension

class Patron(IlsRecord):
    _extensions = [
        UserDataExtension(),
        OperationLogObserverExtension(),
    ]
```

In `rero_ils/config.py`, update the config dict:

```python
RERO_ILS_ENABLE_OPERATION_LOG = {
    "documents": "doc",
    "holdings": "hold",
    "items": "item",
    "ill_requests": "illr",
    "local_entities": "locent",
    "patrons": "ptrn",
}
```

This follows the exact same pattern used by Documents, Holdings, Items, ILL Requests, and Local Entities. The extension hooks into `post_create`, `pre_commit`, and `post_delete` to automatically create operation log entries in the `operation_logs-YYYY` ES index.

---

## 3. Add ILL Requests to `get_links_to_me()`

This is a pre-existing gap: active ILL requests are not checked when determining if a patron can be deleted. This must be fixed before implementing the cleanup task, as it also protects against manual patron deletion orphaning active ILL requests.

### File to modify

- `rero_ils/modules/patrons/api.py` — method `get_links_to_me()`

### Change

Add an ILL request check alongside the existing loans and transactions checks:

```python
from rero_ils.modules.ill_requests.api import ILLRequestsSearch

# Inside get_links_to_me(), after the template_query:
ill_query = ILLRequestsSearch().filter(
    "term", patron__pid=self.pid
).filter(
    "terms", status=["pending", "validated"]
)
if get_pids:
    ill_requests = sorted_pids(ill_query)
else:
    ill_requests = ill_query.count()
if ill_requests:
    links["ill_requests"] = ill_requests
```

---

## 4. Celery Task: `task_delete_inactive_patrons`

### Files to modify

- `rero_ils/modules/patrons/tasks.py` — add the new task and helper functions
- `rero_ils/config.py` — register in `CELERY_BEAT_SCHEDULE`

### Task Logic (pseudocode)

```python
@shared_task(ignore_result=True)
def task_delete_inactive_patrons(dry_run=False):
    """Delete inactive patron profiles for all organisations.

    :param dry_run: if True, log candidates without deleting them.
    """
    for org in Organisation.get_all():
        config = org.get("patron_cleanup")
        if not config:
            continue
        _delete_inactive_patrons_for_org(org, config, dry_run=dry_run)
    _cleanup_orphaned_users(dry_run=dry_run)
    set_timestamp("delete_inactive_patrons")


def _delete_inactive_patrons_for_org(org, config, dry_run=False):
    """Process one organisation's inactive patron cleanup."""
    now = datetime.now()
    expiration_cutoff = add_years(now, -config["expiration_years"])
    inactivity_cutoff = add_years(now, -config["inactivity_years"])
    excluded_ptty_pids = set(config.get("excluded_patron_types", []))

    # ES query: find candidate patrons in this org
    # Pre-filter: patron role, expired, not blocked, not professional
    query = (
        PatronsSearch()
        .filter("term", organisation__pid=org.pid)
        .filter("term", roles="patron")
        .filter("range", patron__expiration_date={
            "lt": expiration_cutoff.strftime("%Y-%m-%d")
        })
        .exclude("term", patron__blocked=True)
        .exclude("terms", roles=list(UserRole.PROFESSIONAL_ROLES))
        .source(["pid", "patron.type.pid", "user_id"])
    )

    deleted = 0
    skipped = 0
    for hit in query.scan():
        # Criterion: patron_type not in exclusion list
        ptty_pid = hit.patron.type.pid
        if ptty_pid in excluded_ptty_pids:
            skipped += 1
            continue

        # Criterion: last connection date
        patron = Patron.get_record_by_pid(hit.pid)
        user = patron.user
        last_login = user.current_login_at or user.last_login_at
        if last_login and last_login > inactivity_cutoff:
            skipped += 1
            continue

        # Criterion: no active links (loans, open transactions, ILL
        # requests, templates)
        links = patron.get_links_to_me()
        if links:
            skipped += 1
            continue

        # Criterion: no non-anonymized historical loans
        non_anon_count = (
            LoansSearch()
            .filter("term", to_anonymize=False)
            .filter("terms", state=[
                LoanState.CANCELLED, LoanState.ITEM_RETURNED
            ])
            .filter("term", patron_pid=patron.pid)
            .count()
        )
        if non_anon_count:
            skipped += 1
            continue

        # All criteria met
        if dry_run:
            current_app.logger.info(
                f"[DRY RUN] Would delete patron {patron.pid} "
                f"(org={org.pid})"
            )
        else:
            patron.delete(force=False, dbcommit=True, delindex=True)
        deleted += 1

    current_app.logger.info(
        f"Patron cleanup for org {org.pid}: "
        f"deleted={deleted}, skipped={skipped}"
        f"{' (dry run)' if dry_run else ''}"
    )


def _cleanup_orphaned_users(dry_run=False):
    """Delete Invenio user accounts that have no patron records."""
    # Query all user_ids that still have at least one patron
    patron_user_ids = set()
    for hit in PatronsSearch().source("user_id").scan():
        patron_user_ids.add(hit.user_id)

    # Find all users and delete those with no patron
    deleted = 0
    ds = current_app.extensions["security"].datastore
    for user in User.query.all():
        if user.id not in patron_user_ids:
            if dry_run:
                current_app.logger.info(
                    f"[DRY RUN] Would delete orphaned user {user.id}"
                )
            else:
                delete_user_sessions(user)
                ds.delete_user(user)
            deleted += 1

    if deleted:
        if not dry_run:
            ds.commit()
        current_app.logger.info(
            f"Orphaned user cleanup: deleted={deleted}"
            f"{' (dry run)' if dry_run else ''}"
        )
```

### Key design decisions

1. **ES pre-filter, then DB verification**: Use an ES query to narrow down candidates (org, roles, expiration_date, not blocked, no professional roles). Then load each patron from DB for the remaining checks that require DB access (last_login, links_to_me, non-anonymized loans).

2. **`last_login` access**: The Invenio `User` model tracks login via `current_login_at` and `last_login_at` on the `accounts_user_login_information` table (Flask-Security trackable is enabled). Access: `patron.user.current_login_at`. If a user has NEVER logged in, both fields will be `None` — this patron is eligible for deletion (treat `None` as "infinitely old").

3. **`blocked` handling**: Only explicit `blocked=true` prevents deletion. If `blocked` is `False` or absent, the patron is eligible. The ES query uses `.exclude("term", patron__blocked=True)` to handle both cases.

4. **Professional roles exclusion**: The ES query uses `.exclude("terms", roles=list(UserRole.PROFESSIONAL_ROLES))` to skip any patron who has a professional role. Only pure `["patron"]`-role accounts are eligible.

5. **Non-anonymized loans check**: Skip patrons who still have returned/cancelled loans with `to_anonymize=False`. The daily loan anonymizer should clear these, but this check prevents deleting a patron before their loan history is properly anonymized.

6. **`_remove_roles()` is not needed**: The existing `Patron.delete()` calls `_remove_roles()`, which modifies Invenio user roles. Since Invenio user roles are independent from patron roles, this step is unnecessary. However, for this task, it's harmless: we only delete pure patron-role accounts, and the user account itself gets cleaned up by `_cleanup_orphaned_users()` afterward. No change to `Patron.delete()` is needed.

7. **Dry-run mode**: The `dry_run` parameter logs all candidates that would be deleted without actually deleting them. Useful for production testing before enabling the task.

8. **Orphaned user cleanup**: After patron deletion, a second pass finds all Invenio user accounts with no remaining patron records and deletes them. This uses Flask-Security's `datastore.delete_user()` which cascades to `accounts_user_login_information`, `accounts_user_session_activity`, `accounts_userrole`, `oauth2server_token`, `oauth2server_client`, and `accounts_useridentity` (all have `ondelete="CASCADE"`). Active sessions are explicitly cleared via `delete_user_sessions()` before deletion.

### Schedule configuration

Add to `CELERY_BEAT_SCHEDULE` in `config.py`:

```python
"celery.delete-inactive-patrons": {
    "task": "rero_ils.modules.patrons.tasks.task_delete_inactive_patrons",
    "schedule": schedules.crontab(minute=0, hour=4, day_of_month="1"),
    "enabled": False,
},
```

Monthly execution on the 1st, at 04:00 UTC (outside peak hours). Disabled by default (enabled per deployment).

---

## 5. Impact Analysis: What Happens When a Patron Is Deleted

### 5.1 Deletion mechanism (`Patron.delete()`)

The current flow (in `rero_ils/modules/patrons/api.py:166-169`):

1. `_remove_roles()` — modifies Invenio user roles. Not strictly needed since user roles are independent from patron roles, but harmless for the cleanup task since the user account is deleted afterward.
2. `IlsRecord.delete()` — calls `can_delete` (safety net), marks PID as deleted, removes from ES, commits to DB.
3. `OperationLogObserverExtension.post_delete` — (newly wired) creates an operation log entry recording the deletion.

The task does NOT use `force=True`. The built-in `can_delete` check via `reasons_not_to_delete()` acts as a safety net on top of the task's own pre-checks.

### 5.2 Loans

- **Active loans**: Prevented by `get_links_to_me()`.
- **Non-anonymized historical loans**: The task explicitly skips patrons with returned/cancelled loans where `to_anonymize=False`. This ensures the loan anonymizer has fully processed the patron's loan history before deletion.
- **Anonymized historical loans**: Already have their patron data anonymized in operation logs. The `patron_pid` field remains in the loan record but the patron data in operation logs is replaced with "anonymized". No impact.

### 5.3 Patron Transactions

- **Open transactions**: Prevented by `get_links_to_me()`.
- **Closed transactions**: Remain in ES with denormalized patron data captured at transaction time. No impact — these are settled historical records.

### 5.4 ILL Requests

- **Active (pending/validated)**: Prevented by the new `get_links_to_me()` check (see section 3).
- **Closed/denied**: Remain in ES with orphaned `patron.$ref`. No functional impact.

### 5.5 Templates

- Checked by `get_links_to_me()`. Only relevant for professional users, not for the cleanup task (which only targets pure patron-role accounts).

### 5.6 Notifications

- Reference patrons indirectly through loans/transactions. Processed quickly. No impact from monthly cleanup.

### 5.7 Operation Logs

- Store **denormalized snapshots** (name, age, patron_type, hashed_pid, postal_code, gender). Immutable historical records. Deleting the patron does not affect operation log integrity.
- **Statistics**: `NumberOfPatronsCfg` aggregates from the ES patron index (deleting a patron correctly removes it from current counts). `NumberOfActivePatronsCfg` uses `hashed_pid` from operation logs (unaffected by patron deletion).

### 5.8 Invenio User Account

- Cleaned up by `_cleanup_orphaned_users()` after patron deletion.
- `datastore.delete_user()` cascades to all related tables (login info, sessions, roles, OAuth tokens, identities).
- If a user has patron accounts in multiple organisations, the user is only deleted when ALL their patron accounts have been deleted.

---

## 6. Testing

### File to create

- `tests/api/patrons/test_patrons_tasks.py`

### Test cases

1. **Patron meets all deletion criteria** — verify patron is deleted and operation log is created.
2. **Patron has active loans** — verify patron is NOT deleted.
3. **Patron has open transactions** — verify patron is NOT deleted.
4. **Patron has active ILL requests** (pending/validated) — verify patron is NOT deleted.
5. **Patron has non-anonymized returned loans** — verify patron is NOT deleted.
6. **Patron is blocked** (`blocked=true`) — verify patron is NOT deleted.
7. **Patron type is in exclusion list** — verify patron is NOT deleted.
8. **Patron's expiration_date is recent** (within threshold) — verify NOT deleted.
9. **User's last login is recent** (within threshold) — verify NOT deleted.
10. **User has never logged in** (`last_login_at` is `None`) — verify patron IS deleted (treated as infinitely old).
11. **Organisation has no `patron_cleanup` config** — verify no action for that org.
12. **Patron with professional roles** — verify NOT deleted.
13. **User with multiple patron accounts** — verify only the eligible account is deleted; user account is preserved as long as other patron accounts exist.
14. **User with no remaining patron accounts** — verify user account is deleted by orphan cleanup.
15. **Dry-run mode** — verify no deletions occur, but candidates are logged.

---

## 7. Summary of All File Changes

| File | Change |
|------|--------|
| `rero_ils/modules/organisations/jsonschemas/organisations/organisation-v0.0.1.json` | Add `patron_cleanup` property |
| `rero_ils/modules/organisations/mappings/v7/organisations/organisation-v0.0.1.json` | Add `patron_cleanup` mapping |
| `rero_ils/modules/patrons/api.py` | Add `OperationLogObserverExtension` to `_extensions`; add ILL requests to `get_links_to_me()` |
| `rero_ils/modules/patrons/tasks.py` | Add `task_delete_inactive_patrons`, `_delete_inactive_patrons_for_org`, `_cleanup_orphaned_users` |
| `rero_ils/config.py` | Add `"patrons": "ptrn"` to `RERO_ILS_ENABLE_OPERATION_LOG`; add beat schedule entry |
| `tests/api/patrons/test_patrons_tasks.py` | Add test cases |
