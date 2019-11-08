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

"""Test utils."""

import os

from rero_ils.modules.utils import read_json_record
from rero_ils.utils import unique_list


def test_unique_list():
    """Test unicity of list."""
    list = ['python', 'snail', 'python', 'snail']
    assert ['python', 'snail'] == unique_list(list)


def test_read_json_record(request):
    """Test IlsRecord PID after validation failed"""
    file_name = os.path.join(request.fspath.dirname, '..', 'data',
                             'documents.json')
    with open(file_name) as json_file:
        count = 0
        for record in read_json_record(json_file):
            count += 1
            assert record.get('pid') == str(count)
        assert count == 2
