# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2023 RERO
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

"""Message."""

from click.testing import CliRunner

from rero_ils.filter import message_filter
from rero_ils.modules.cli.messages import delete, get, info, set_message
from rero_ils.modules.messages import Message


def test_message(app):
    """Test message."""
    key = "test_fr"
    message = "Foo bar"
    result = {"type": "success", "message": message}

    assert Message.set(key=key, type="success", value=message)
    assert Message.get(key) == result
    assert Message.delete(key)
    assert Message.get(key) is None


def test_message_filter(app):
    """Test message filter."""
    key = "test_en"
    message = "Filter"
    result = {"type": "success", "message": message}

    assert Message.set(key=key, type="success", value=message)
    assert message_filter(key) == result
    assert Message.delete(key)


def test_message_cli(app):
    """Test message cli."""
    runner = CliRunner()
    result = runner.invoke(set_message, ["MYKEY", "MYTYPE", "MY MESSAGE"])
    assert result.exit_code == 0
    assert result.output.strip().split("\n") == [
        'OK: MYKEY               MYTYPE         "MY MESSAGE"'
    ]

    runner = CliRunner()
    result = runner.invoke(get, ["MYKEY"])
    assert result.exit_code == 0
    assert result.output.strip().split("\n") == [
        'MYKEY               MYTYPE         "MY MESSAGE"'
    ]

    runner = CliRunner()
    result = runner.invoke(get, ["NOKEY"])
    assert result.exit_code == 1
    assert result.output.strip().split("\n") == ["NOKEY               KEY NOT FOUND!"]

    runner = CliRunner()
    result = runner.invoke(info)
    assert result.exit_code == 0
    assert result.output.strip().split("\n") == [
        "KEY                 TYPE           MESSAGE",
        'MYKEY               MYTYPE         "MY MESSAGE"',
    ]

    runner = CliRunner()
    result = runner.invoke(delete, ["MYKEY", "--yes-i-know"])
    assert result.exit_code == 0
    assert result.output.strip().split("\n") == ["MYKEY               DELETED"]

    runner = CliRunner()
    result = runner.invoke(info)
    assert result.exit_code == 0
    assert result.output.strip().split("\n") == [
        "KEY                 TYPE           MESSAGE"
    ]
