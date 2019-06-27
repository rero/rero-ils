# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019  RERO
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Test utils."""

from rero_ils.utils import unique_list


def test_unique_list():
    """Test unicity of list."""
    list = ['python', 'snail', 'python', 'snail']
    assert ['python', 'snail'] == unique_list(list)
