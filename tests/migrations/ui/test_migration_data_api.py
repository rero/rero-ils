# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021-2024 RERO
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Migration Record tests."""

import pytest
from elasticsearch import NotFoundError
from elasticsearch_dsl import Index
from elasticsearch_dsl.exceptions import ValidationException


def test_migration_data_create(migration, migration_xml_data, lib_martigny):
    """Test the migration creation."""

    raw = migration_xml_data.encode()
    data = dict(raw=raw, migration_id=migration.meta.id)
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
    assert lib_martigny.get_links_to_me(get_pids=True) == {
        "migrations": [migration.name]
    }
