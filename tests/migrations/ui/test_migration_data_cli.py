# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
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

"""Test cli."""


from os.path import dirname, join

from click.testing import CliRunner

from rero_ils.modules.migrations.data.cli import dedup, get, load, subsets


def test_migrations_cli(app, migration):
    """Test validate cli."""
    runner = CliRunner()
    file_name = join(dirname(__file__), "../../data/migration.xml")
    res = runner.invoke(load, [migration.name, file_name, "-n"])
    assert res.exit_code == 0

    res = runner.invoke(get, [migration.name, "-f", "ids"])
    assert res.output == ""
    assert res.exit_code == 0

    res = runner.invoke(load, [migration.name, file_name])
    assert res.exit_code == 0

    res = runner.invoke(get, [migration.name, "-f", "ids"])
    assert "R003448321" in res.output
    assert res.exit_code == 0

    res = runner.invoke(dedup, [migration.name, "-n"])
    assert "R003448321" in res.output
    assert "Status" in res.output
    assert res.exit_code == 0

    res = runner.invoke(dedup, [migration.name])
    assert res.exit_code == 0

    res = runner.invoke(subsets, [migration.name, "set1"])
    assert "1 record" in res.output
    assert res.exit_code == 0
