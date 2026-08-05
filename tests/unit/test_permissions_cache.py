# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Record permissions cache tests."""

from unittest.mock import patch

from invenio_db import db
from sqlalchemy import text

from rero_ils.modules.permissions_cache import (
    delete_record_permissions_cache,
    record_permissions_cache_key,
    register_record_permissions_cache_deletion,
)


def test_record_permissions_cache_key():
    """Test record permissions cache key creation."""
    assert record_permissions_cache_key("documents", "doc1") == "/permissions/documents/doc1"
    assert record_permissions_cache_key("documents") == "/permissions/documents"


@patch("rero_ils.modules.permissions_cache.current_cache.delete")
def test_delete_record_permissions_cache(cache_delete, appctx):
    """Test deleting a record permissions cache entry."""
    delete_record_permissions_cache("documents", "doc1")

    cache_delete.assert_called_once_with("/permissions/documents/doc1")


@patch("rero_ils.modules.permissions_cache.delete_record_permissions_cache")
def test_delete_record_permissions_cache_after_commit(cache_delete, appctx):
    """Test deleting a record permissions cache entry after commit."""
    db.session.execute(text("SELECT 1"))
    register_record_permissions_cache_deletion("documents", "doc1")

    with db.session.begin_nested():
        pass
    cache_delete.assert_not_called()

    db.session.commit()
    cache_delete.assert_called_once_with("documents", "doc1")


@patch("rero_ils.modules.permissions_cache.delete_record_permissions_cache")
def test_cancel_record_permissions_cache_deletion_after_rollback(cache_delete, appctx):
    """Test cancelling a record permissions cache deletion after rollback."""
    db.session.execute(text("SELECT 1"))
    register_record_permissions_cache_deletion("documents", "doc1")

    db.session.rollback()
    db.session.commit()

    cache_delete.assert_not_called()
