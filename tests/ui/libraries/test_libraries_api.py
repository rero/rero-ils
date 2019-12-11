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

"""Library Record tests."""

from __future__ import absolute_import, print_function

import pytz
from dateutil import parser

from rero_ils.modules.libraries.api import Library
from rero_ils.modules.libraries.api import library_id_fetcher as fetcher
from rero_ils.modules.utils import date_string_to_utc


def test_library_create(db, lib_martigny_data):
    """Test library creation."""
    lib = Library.create(lib_martigny_data, delete_pid=True)
    assert lib == lib_martigny_data
    assert lib.get('pid') == '1'

    lib = Library.get_record_by_pid('1')
    assert lib == lib_martigny_data

    fetched_pid = fetcher(lib.id, lib)
    assert fetched_pid.pid_value == '1'
    assert fetched_pid.pid_type == 'lib'


def test_libraries_is_open(lib_martigny):
    """Test library creation."""
    saturday = '2018-12-15 11:00'
    library = lib_martigny
    assert library.is_open(date=saturday)

    assert not library.is_open(date_string_to_utc('2019-08-01'))
    assert not library.is_open(date_string_to_utc('2222-8-1'))

    del library['exception_dates']
    library.replace(library.dumps(), dbcommit=True)

    monday = '2018-12-10 08:00'
    assert library.is_open(date=monday)
    monday = '2018-12-10 06:00'
    assert not library.is_open(date=monday)

    assert library.next_open(
        date=saturday
    ).date() == parser.parse('2018-12-17').date()
    assert library.next_open(
        date=saturday,
        previous=True
    ).date() == parser.parse('2018-12-14').date()

    assert library.count_open(start_date=monday, end_date=saturday) == 5
    assert library.in_working_days(
        count=5,
        date=date_string_to_utc('2018-12-10')
    ) == date_string_to_utc('2018-12-17')

    assert not library.is_open(date=saturday)


def test_library_can_delete(lib_martigny):
    """Test can delete."""
    assert lib_martigny.get_links_to_me() == {}
    assert lib_martigny.can_delete


def test_library_timezone(lib_martigny):
    """Test library timezone."""
    tz = lib_martigny.get_timezone()
    assert tz == pytz.timezone('Europe/Zurich')
