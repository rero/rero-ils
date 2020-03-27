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
from datetime import datetime

from rero_ils.modules.patrons.api import Patron
from rero_ils.modules.utils import add_years, get_schema_for_resource, \
    read_json_record
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


def test_add_years():
    """Test adding years to a date."""
    initial_date = datetime.now()
    one_year_later = add_years(initial_date, 1)
    assert initial_date.year == one_year_later.year - 1

    initial_date = datetime.strptime('2020-02-29', '%Y-%m-%d')
    tow_years_later = add_years(initial_date, 2)
    four_years_later = add_years(initial_date, 4)
    assert tow_years_later.month == 3 and tow_years_later.day == 1
    assert four_years_later.month == initial_date.month and \
        four_years_later.day == initial_date.day


def test_get_schema_for_resources(app):
    """Test get_schemas_for_resource function."""
    json_schema = 'https://ils.rero.ch/schema/patrons/patron-v0.0.1.json'
    assert get_schema_for_resource(Patron) == json_schema
    assert get_schema_for_resource('ptrn') == json_schema
