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

"""Minters module tests."""

from __future__ import absolute_import, print_function

from dateutil import parser

from rero_ils.modules.libraries.api import Library


def test_libraries_is_open(app, minimal_library_record, exception_dates):
    """Test library creat."""
    lib = Library.create(minimal_library_record, dbcommit=True, reindex=True)
    monday = '2018-12-10 08:00'
    assert lib.is_open(date=monday)
    monday = '2018-12-10 06:00'
    assert not lib.is_open(date=monday)

    saturday = '2018-12-15 11:00'
    assert lib.next_open(
        date=saturday
    ).date() == parser.parse('2018-12-17').date()
    assert lib.next_open(
        date=saturday,
        previous=True
    ).date() == parser.parse('2018-12-14').date()

    assert lib.count_open(start_date=monday, end_date=saturday) == 5
    assert lib.in_working_days(
        count=5,
        date='2018-12-10'
    ) == parser.parse('2018-12-17')

    assert not lib.is_open(date=saturday)
    lib['exception_dates'] = exception_dates
    lib.update(lib, dbcommit=True, reindex=True)
    assert lib.is_open(date=saturday)

    assert not lib.is_open(date='2018-8-1')
    assert not lib.is_open(date='2222-8-1')
