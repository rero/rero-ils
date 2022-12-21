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

from rero_ils.filter import message_filter
from rero_ils.modules.message import Message


def test_message(app):
    """Test message."""
    key = 'test_fr'
    message = 'Foo bar'
    result = {'type': 'success', 'message': message}

    assert Message.set(key=key, type='success', value=message)
    assert Message.get(key) == result
    assert Message.delete(key)
    assert Message.get(key) is None


def test_message_filter(app):
    """Test message filter."""
    key = 'test_en'
    message = 'Filter'
    result = {'type': 'success', 'message': message}

    assert Message.set(key=key, type='success', value=message)
    assert message_filter(key) == result
