# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Migration Record tests."""

import pytest
from invenio_search.engine import dsl, search

from rero_ils.modules.migrations.data.api import Deduplication, DeduplicationCandidate


def test_migration_data_create(migration, migration_xml_data, lib_martigny):
    """Test the migration creation."""
    raw = migration_xml_data.encode()
    data = {"raw": raw, "migration_id": migration.meta.id}
    MigrationData = migration.data_class
    migration_id = migration.meta.id
    with pytest.raises(dsl.ValidationException):
        MigrationData().save()
    migration_data = MigrationData(**data)
    index = dsl.Index(migration.data_index_name)
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
    with pytest.raises(search.NotFoundError):
        assert MigrationData.get(migration.meta.id)
    assert MigrationData.search().count() == 0


def test_migration_data_detailed_score(migration, migration_xml_data):
    """Test candidates scored by an integer and a float on the same criterion."""
    MigrationData = migration.data_class
    candidates = [
        DeduplicationCandidate(
            pid=pid, json={"pid": pid}, score=value, detailed_score={"extent": {"value": value, "weight": 2.0}}
        )
        for pid, value in (("1", 1), ("2", 0.5))
    ]
    migration_data = MigrationData(
        raw=migration_xml_data.encode(),
        migration_id=migration.meta.id,
        deduplication=Deduplication(status="check", candidates=candidates),
    )
    assert migration_data.save() == "created"
    dsl.Index(migration.data_index_name).refresh()
    candidates = MigrationData.get(migration_data.meta.id).deduplication.candidates
    assert [candidate.detailed_score.extent.value for candidate in candidates] == [1, 0.5]
    migration_data.delete()


def test_migrations_library_get_links_to_me(lib_martigny, migration):
    """Test library links."""
    assert lib_martigny.get_links_to_me().get("migrations") == 1
    assert lib_martigny.get_links_to_me(get_pids=True) == {"migrations": [migration.name]}
