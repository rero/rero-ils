# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Migration Record tests."""

import pytest
from elasticsearch import NotFoundError
from elasticsearch_dsl import Index
from elasticsearch_dsl.exceptions import ValidationException

from rero_ils.modules.migrations.api import Migration


def test_migrations_create(search_indices, lib_martigny):
    """Test the migration creation."""
    with pytest.raises(ValidationException):
        Migration().save()
    with pytest.raises(ValidationException):
        Migration(name="name").save()
    with pytest.raises(ValidationException):
        Migration(name="name", library_pid="2", status="invalid").save()
    migration = Migration(
        name="name",
        library_pid=lib_martigny.pid,
        conversion_code="tests.mock_modules.Converter",
    )
    assert migration.library
    assert migration.conversion_class.convert
    index = Index(Migration.Index.name)
    assert migration.save() == "created"
    assert migration.meta.id
    assert Migration.get(migration.meta.id)
    assert Migration.exists(migration.meta.id)
    index.refresh()
    assert Migration.search().count() > 0
    migration.description = "foo"
    assert migration.save() == "updated"
    assert Migration.get(migration.meta.id).description == "foo"
    migration.delete()
    assert not Migration.exists(migration.meta.id)
    with pytest.raises(NotFoundError):
        assert Migration.get(migration.meta.id)
    index.refresh()
    assert Migration.search().count() == 0


def test_migrations_library_get_links_to_me(lib_martigny, migration):
    """Test library links."""
    assert lib_martigny.get_links_to_me().get("migrations") == 1
    assert lib_martigny.get_links_to_me(get_pids=True) == {"migrations": [migration.name]}
