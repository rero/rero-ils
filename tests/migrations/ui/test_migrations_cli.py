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

from click.testing import CliRunner

from rero_ils.modules.migrations.cli import create, delete, destroy, get, init, update


def test_migrations_cli(app, lib_martigny):
    """Test validate cli."""
    runner = CliRunner()
    res = runner.invoke(init, [])
    assert res.exit_code == 0

    res = runner.invoke(get, [])
    assert "Aborted" in res.output
    assert res.exit_code == 1

    runner = CliRunner()
    res = runner.invoke(
        create,
        [
            "test",
            lib_martigny.pid,
            "scripts.convert_marc21xml.Marc21XMLConverter",
            "-d",
            "description",
        ],
    )
    assert res.exit_code == 0

    res = runner.invoke(get, ["-n", "test"])
    assert "test" in res.output
    assert res.exit_code == 0

    res = runner.invoke(get, ["-n", "foo"])
    assert "Aborted" in res.output
    assert res.exit_code == 1

    res = runner.invoke(update, ["foo", "-d", "new description"])
    assert res.exit_code == 1

    res = runner.invoke(
        update,
        [
            "test",
            "-d",
            "new description",
            "-s",
            "done",
            "-l",
            lib_martigny.pid,
            "-c",
            "newscript.py",
        ],
    )
    assert res.exit_code == 0

    res = runner.invoke(delete, ["test", "--yes-i-know"])
    assert res.exit_code == 0

    res = runner.invoke(destroy, ["--yes-i-know"])
    assert res.exit_code == 0
