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

"""Test csv creation, import et export."""

from os.path import dirname, join

import mock
from click.testing import CliRunner
from utils import mock_response

from rero_ils.modules.cli.fixtures import count_cli, create


def test_count(app, script_info):
    """Test count cli."""
    json_file_name = join(dirname(__file__), '../data/documents.json')

    runner = CliRunner()
    result = runner.invoke(
        count_cli,
        [json_file_name],
        obj=script_info
    )
    assert result.exit_code == 0
    assert result.output.strip().split('\n')[1] == 'Count: 2'

    runner = CliRunner()
    result = runner.invoke(
        count_cli,
        [json_file_name, '-l'],
        obj=script_info
    )
    assert result.exit_code == 0
    assert result.output.strip().split('\n')[1] == 'Count: 2'


@mock.patch('requests.Session.get')
def test_create(mock_contributions_mef_get, app, script_info,
                entity_person_response_data):
    """Test create cli."""
    json_file_name = join(dirname(__file__), '../data/documents.json')
    mock_contributions_mef_get.return_value = mock_response(
        json_data=entity_person_response_data
    )

    runner = CliRunner()
    result = runner.invoke(
        create,
        [json_file_name, '--pid_type', 'doc', '--append', '--reindex',
         '--dbcommit', '--verbose', '--debug', '--lazy', '--dont-stop'],
        obj=script_info
    )
    # assert result.exit_code == 0
    assert result.output.strip().split('\n')[3:] == [
        'DB commit: 2',
        'Append fixtures new identifiers: 2',
        'DB commit append: 2'
    ]

    runner = CliRunner()
    result = runner.invoke(
        create,
        [json_file_name, '--pid_type', 'doc', '--append', '--reindex',
         '--dbcommit', '--verbose', '--debug', '--lazy', '--dont-stop',
         '--create_or_update'],
        obj=script_info
    )
    # assert result.exit_code == 0
    assert result.output.strip().split('\n')[3:] == [
        'DB commit: 2',
        'Append fixtures new identifiers: 0',
        'DB commit append: 0'
    ]
