# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test csv creation, import et export."""

from os.path import dirname, join
from unittest import mock

from click.testing import CliRunner

from rero_ils.modules.cli.fixtures import count_cli, create
from tests.utils import mock_response


def test_count(app):
    """Test count cli."""
    json_file_name = join(dirname(__file__), "../data/documents.json")

    runner = CliRunner()
    result = runner.invoke(count_cli, [json_file_name])
    assert result.exit_code == 0
    assert result.output.strip().split("\n")[1] == "Count: 2"

    runner = CliRunner()
    result = runner.invoke(count_cli, [json_file_name, "-l"])
    assert result.exit_code == 0
    assert result.output.strip().split("\n")[1] == "Count: 2"


@mock.patch("requests.Session.get")
def test_create(mock_contributions_mef_get, app, entity_person_response_data):
    """Test create cli."""
    json_file_name = join(dirname(__file__), "../data/documents.json")
    mock_contributions_mef_get.return_value = mock_response(json_data=entity_person_response_data)

    runner = CliRunner()
    result = runner.invoke(
        create,
        [
            json_file_name,
            "--pid_type",
            "doc",
            "--append",
            "--reindex",
            "--dbcommit",
            "--verbose",
            "--debug",
            "--lazy",
            "--dont-stop",
        ],
    )
    # assert result.exit_code == 0
    assert result.output.strip().split("\n")[3:] == [
        "DB commit: 2",
        "Append fixtures new identifiers: 2",
        "DB commit append: 2",
    ]

    runner = CliRunner()
    result = runner.invoke(
        create,
        [
            json_file_name,
            "--pid_type",
            "doc",
            "--append",
            "--reindex",
            "--dbcommit",
            "--verbose",
            "--debug",
            "--lazy",
            "--dont-stop",
            "--create_or_update",
        ],
    )
    # assert result.exit_code == 0
    assert result.output.strip().split("\n")[3:] == [
        "DB commit: 2",
        "Append fixtures new identifiers: 0",
        "DB commit append: 0",
    ]
