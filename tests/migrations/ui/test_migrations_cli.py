# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test cli."""

from click.testing import CliRunner
from elasticsearch_dsl import Index

from rero_ils.modules.migrations.api import Migration
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

    index = Index(Migration.Index.name)
    index.refresh()

    res = runner.invoke(destroy, ["--yes-i-know"])
    assert res.exit_code == 0
