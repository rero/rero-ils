# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
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

"""Common pytest fixtures and plugins."""

import pytest
from elasticsearch_dsl import Index

from rero_ils.modules.migrations.api import Migration


@pytest.fixture(scope="module")
def migration(es_indices, lib_martigny):
    """Migration fixture."""
    data = dict(name="name", library_pid=str(lib_martigny.pid))
    index = Index(Migration.Index.name)
    migration = Migration(meta={"id": data["name"]}, **data)
    migration.save()
    index.refresh()
    yield migration
    migration.delete()
    index.refresh()


@pytest.fixture(scope="module")
def es_indices(app):
    """Create test app."""
    Migration.init()
    yield
    Index(Migration.Index.name).delete()
