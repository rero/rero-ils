# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Migration Record tests."""

import pytest
from elasticsearch import NotFoundError
from elasticsearch_dsl import Index
from elasticsearch_dsl.exceptions import ValidationException


def test_migration_data_create(migration, migration_xml_data, lib_martigny):
    """Test the migration creation."""

    raw = migration_xml_data.encode()
    data = {"raw": raw, "migration_id": migration.meta.id}
    MigrationData = migration.data_class
    migration_id = migration.meta.id
    with pytest.raises(ValidationException):
        MigrationData().save()
    migration_data = MigrationData(**data)
    index = Index(migration.data_index_name)
    assert migration_data.save() == "created"
    assert migration_data.conversion.json.title
    index.refresh()
    data_id = migration_data.meta.id
    assert data_id
    assert MigrationData.get(data_id)
    assert MigrationData.exists(data_id)
    assert MigrationData.search().count() > 0

    migration_data.delete()
    index.refresh()
    assert not MigrationData.exists(data_id)
    with pytest.raises(NotFoundError):
        assert MigrationData.get(migration.meta.id)
    assert MigrationData.search().count() == 0


def test_migrations_library_get_links_to_me(lib_martigny, migration):
    """Test library links."""
    assert lib_martigny.get_links_to_me().get("migrations") == 1
    assert lib_martigny.get_links_to_me(get_pids=True) == {"migrations": [migration.name]}
