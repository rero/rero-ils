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

from rero_ils.modules.cli import check_validate, tokens_create


def test_cli_validate(app, script_info):
    """Test validate cli."""
    runner = CliRunner()
    file_name = join(dirname(__file__), '../data/documents.json')

    res = runner.invoke(
        check_validate,
        [file_name, 'doc', '-v'],
        obj=script_info
    )
    assert res.output.strip().split('\n') == [
        'Testing json schema for file',
        '\tTest record: 1',
        '\tTest record: 2'
    ]


def test_cli_access_token(app, script_info, patron_martigny):
    """Test access token cli."""
    runner = CliRunner()
    res = runner.invoke(
        tokens_create,
        ['-n', 'test', '-u', patron_martigny.get('email'),
         '-t', 'my_token'],
        obj=script_info
    )
    assert res.output.strip().split('\n') == ['my_token']
