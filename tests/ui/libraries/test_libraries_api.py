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


def test_library_create(db, library_data):
    """Test libanisation creation."""
    lib = Library.create(library_data, delete_pid=True)
    assert lib == library_data
    assert lib.get('pid') == '1'

    lib = Library.get_record_by_pid('1')
    assert lib == library_data

    fetched_pid = fetcher(lib.id, lib)
    assert fetched_pid.pid_value == '1'
    assert fetched_pid.pid_type == 'lib'


def test_library_es_mapping(es_clear, db, library_data, organisation):
    """."""
    search = LibrariesSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping
    Library.create(library_data, dbcommit=True, reindex=True, delete_pid=True)
    assert mapping == get_mapping(search.Meta.index)


def test_libraries_is_open(library):
    """Test library creat."""
    saturday = '2018-12-15 11:00'
    assert library.is_open(date=saturday)

    assert not library.is_open(date='2018-8-1')
    assert not library.is_open(date='2222-8-1')

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


def test_library_can_delete(library):
    """Test can  delete"""
    assert library.get_links_to_me() == {}
    assert library.can_delete
