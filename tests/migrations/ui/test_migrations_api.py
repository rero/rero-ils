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

from rero_ils.modules.migrations.api import Migration


def test_migrations_create(es_indices, lib_martigny):
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
        conversion_code="mock_modules.Converter",
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
    assert lib_martigny.get_links_to_me(get_pids=True) == {
        "migrations": [migration.name]
    }
