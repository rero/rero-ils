# -*- coding: utf-8 -*-
#
# This file is part of RERO ILS.
# Copyright (C) 2017 RERO.
#
# RERO ILS is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# RERO ILS is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RERO ILS; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Library Record tests."""

from __future__ import absolute_import, print_function

from dateutil import parser
from utils import get_mapping

from rero_ils.modules.libraries.api import LibrariesSearch, Library
from rero_ils.modules.libraries.api import library_id_fetcher as fetcher


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

    assert not library.is_open(date=parser.parse('2019-08-01'))
    assert not library.is_open(date=parser.parse('2222-8-1'))

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
        date='2018-12-10'
    ) == parser.parse('2018-12-17')

    assert not library.is_open(date=saturday)


def test_library_can_delete(lib_martigny):
    """Test can delete."""
    assert lib_martigny.get_links_to_me() == {}
    assert lib_martigny.can_delete
