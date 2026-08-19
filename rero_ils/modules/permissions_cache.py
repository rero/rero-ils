# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Helpers for record permissions cache."""

from flask import request
from invenio_cache import current_cache
from invenio_db import db
from sqlalchemy import event
from sqlalchemy.orm import Session

_AFTER_COMMIT_DELETIONS = "record_permissions_cache_after_commit_deletions"


def record_permissions_cache_key(route_name=None, record_pid=None):
    """Build the cache key for record permissions."""
    if route_name is None:
        route_name = request.view_args["route_name"]
        record_pid = request.view_args.get("record_pid")
    cache_key = f"/permissions/{route_name}"
    return f"{cache_key}/{record_pid}" if record_pid else cache_key


def delete_record_permissions_cache(route_name, record_pid=None):
    """Delete a record permissions cache entry."""
    return current_cache.delete(record_permissions_cache_key(route_name, record_pid))


def register_record_permissions_cache_deletion(route_name, record_pid=None):
    """Register a record permissions cache deletion after commit."""
    deletions = db.session.info.setdefault(_AFTER_COMMIT_DELETIONS, set())
    deletions.add((route_name, record_pid))


@event.listens_for(Session, "after_commit")
def _delete_record_permissions_cache_after_commit(session):
    """Delete registered cache entries after the outer transaction commits."""
    if session.in_nested_transaction():
        return
    deletions = session.info.pop(_AFTER_COMMIT_DELETIONS, set())
    for route_name, record_pid in deletions:
        delete_record_permissions_cache(route_name, record_pid)


@event.listens_for(Session, "after_rollback")
def _discard_record_permissions_cache_deletions_after_rollback(session):
    """Discard registered cache deletions after the outer transaction rolls back."""
    if not session.in_nested_transaction():
        session.info.pop(_AFTER_COMMIT_DELETIONS, None)
