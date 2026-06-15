# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

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
