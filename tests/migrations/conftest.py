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
    data = dict(
        name="name",
        library_pid=str(lib_martigny.pid),
        conversion_code="mock_modules.Converter",
    )
    index = Index(Migration.Index.name)
    migration = Migration(**data)
    migration.save()
    index.refresh()
    yield migration
    migration.delete()
    index.refresh()


@pytest.fixture(scope="module")
def migration_xml_data():
    """Marc21 xml data."""
    yield """
    <record>
      <datafield tag="100" ind1=" " ind2=" ">
        <subfield code="a">Jean-Paul</subfield>
        <subfield code="b">II</subfield>
        <subfield code="c">Pape</subfield>
        <subfield code="d">1954-</subfield>
        <subfield code="4">aut</subfield>
      </datafield>
      <datafield tag="240" ind1=" " ind2=" ">
        <subfield code="a">Treaties, etc.</subfield>
      </datafield>
      <datafield tag="700" ind1=" " ind2=" ">
        <subfield code="a">Dumont, Jean</subfield>
        <subfield code="c">Historien</subfield>
        <subfield code="d">1921-2014</subfield>
        <subfield code="4">edt</subfield>
      </datafield>
      <datafield tag="700" ind1="1" ind2=" ">
        <subfield code="a">Santamaría, Germán</subfield>
        <subfield code="t">No morirás</subfield>
        <subfield code="l">français</subfield>
      </datafield>
      <datafield tag="710" ind1=" " ind2=" ">
        <subfield code="a">RERO</subfield>
      </datafield>
      <datafield tag="711" ind1="2" ind2=" ">
        <subfield code="a">Biennale de céramique contemporaine</subfield>
        <subfield code="n">(17 :</subfield>
        <subfield code="d">2003 :</subfield>
        <subfield code="c">Châteauroux)</subfield>
      </datafield>
      <datafield tag="730" ind1="0" ind2=" ">
        <subfield code="a">Bible.</subfield>
        <subfield code="n">000.</subfield>
        <subfield code="p">A.T. et N.T. :</subfield>
        <subfield code="l">Coréen</subfield>
      </datafield>
    </record>
    """


@pytest.fixture(scope="module")
def migration_data(migration_xml_data, migration):
    """Simple migration data."""
    data = dict(raw=migration_xml_data.encode(), migration_id=migration.meta.id)
    MigrationData = migration.data_class
    m_data = MigrationData(**data)
    m_data.save()
    yield m_data
    m_data.delete()


@pytest.fixture(scope="module")
def es_indices(app):
    """Create test app."""
    Migration.init()
    yield
    Index(Migration.Index.name).delete()
