# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Common pytest fixtures and plugins."""

import pytest
from elasticsearch_dsl import Index

from rero_ils.modules.migrations.api import Migration
from rero_ils.modules.migrations.data.api import Deduplication


@pytest.fixture(scope="module")
def migration(search_indices, lib_martigny):
    """Migration fixture."""
    data = {
        "name": "name",
        "library_pid": str(lib_martigny.pid),
        "conversion_code": "tests.mock_modules.Converter",
    }
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
	<leader>00706nas a22002297a 4500</leader>
	<controlfield tag="001">REROILS:778</controlfield>
	<controlfield tag="003">RERO</controlfield>
	<controlfield tag="005">20190705130200.0</controlfield>
	<controlfield tag="008">030401 19049999fr |||m|  ||||0 |  0fre d</controlfield>
	<datafield ind1=" " ind2=" " tag="019">
		<subfield code="a">Réf. bibliogr.: BNF</subfield>
		<subfield code="9">gevbpu/04.2003</subfield>
	</datafield>
	<datafield ind1=" " ind2=" " tag="035">
		<subfield code="a">R003336627</subfield>
	</datafield>
	<datafield ind1=" " ind2="9" tag="039">
		<subfield code="a">201907051302</subfield>
		<subfield code="b">VLOAD</subfield>
		<subfield code="c">201705181242</subfield>
		<subfield code="d">VLOAD</subfield>
		<subfield code="c">200304031430</subfield>
		<subfield code="d">6043</subfield>
		<subfield code="y">200304011433</subfield>
		<subfield code="z">6043</subfield>
	</datafield>
	<datafield ind1=" " ind2=" " tag="040">
		<subfield code="a">RERO gevbpu</subfield>
	</datafield>
	<datafield ind1="0" ind2="0" tag="245">
		<subfield code="a">Nouvelle bibliothèque de chasse</subfield>
	</datafield>
	<datafield ind1=" " ind2="1" tag="264">
		<subfield code="a">Paris :</subfield>
		<subfield code="b">E. Nourry,</subfield>
		<subfield code="c">1904-</subfield>
	</datafield>
	<datafield ind1=" " ind2=" " tag="336">
		<subfield code="b">txt</subfield>
		<subfield code="2">rdacontent</subfield>
	</datafield>
	<datafield ind1=" " ind2=" " tag="337">
		<subfield code="b">n</subfield>
		<subfield code="2">rdamedia</subfield>
	</datafield>
	<datafield ind1=" " ind2=" " tag="338">
		<subfield code="b">nc</subfield>
		<subfield code="2">rdacarrier</subfield>
	</datafield>
	<datafield ind1=" " ind2=" " tag="339">
		<subfield code="a">docmaintype_series</subfield>
	</datafield>
	<datafield ind1=" " ind2=" " tag="900">
		<subfield code="a">noselfmerge</subfield>
	</datafield>
	<datafield ind1=" " ind2=" " tag="900">
		<subfield code="a">reroslsp</subfield>
	</datafield>
</record>
    """


@pytest.fixture(scope="module")
def migration_data(migration_xml_data, migration):
    """Simple migration data."""
    data = {
        "raw": migration_xml_data.encode(),
        "migration_id": migration.meta.id,
        "deduplication": Deduplication(status="pending", subset="set 1", modified_by="system"),
    }
    MigrationData = migration.data_class
    m_data = MigrationData(**data)
    m_data.save()
    yield m_data
    m_data = MigrationData.get(m_data.meta.id)
    m_data.delete()


@pytest.fixture(scope="module")
def search_indices(app):
    """Create test app."""
    Migration.init()
    yield
    Index(Migration.Index.name).delete()
