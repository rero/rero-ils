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

from datetime import datetime, timedelta

import pytz
from dateutil import parser

from rero_ils.modules.libraries.api import Library
from rero_ils.modules.libraries.api import library_id_fetcher as fetcher
from rero_ils.modules.utils import date_string_to_utc


def test_library_create(db, org_martigny, lib_martigny_data):
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
    """Test library 'open' methods."""
    saturday = '2018-12-15 11:00'
    monday = '2018-12-10 06:00'
    library = lib_martigny

    def next_weekday(d, weekday):
        """Get the next weekday after a giver date."""
        # 0=Monday, 1=Tuesday, ...
        days_ahead = weekday - d.weekday()
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        return d + timedelta(days_ahead)

    # CASE 1 :: basic tests. According to library settings:
    #   * monday --> friday  :: 6 AM  --> closed
    #   * monday --> friday  :: 12 AM --> open
    #   * saturday & sunday  :: closed all day
    for day_idx in range(0, 5):
        test_date = next_weekday(datetime.now(), day_idx)
        test_date = test_date.replace(hour=6, minute=0)
        assert not library.is_open(test_date)
        test_date = test_date.replace(hour=12)
        assert library.is_open(test_date)
    test_date = next_weekday(datetime.now(), 5)
    assert not library.is_open(test_date)
    test_date = next_weekday(datetime.now(), 6)
    assert not library.is_open(test_date)

    # CASE 2 :: Check single exception dates
    #   * According to library setting, the '2018-12-15' day is an exception
    #     not repeatable. It's a saturday (normally closed), but defined as
    #     open by exception.
    exception_date = date_string_to_utc('2018-12-15')
    exception_date = exception_date.replace(hour=20, minute=0)
    assert exception_date.weekday() == 5
    assert not library.is_open(exception_date)
    exception_date = exception_date.replace(hour=12, minute=0)
    assert library.is_open(exception_date)
    # previous saturday isn't yet an exception open date
    exception_date = exception_date - timedelta(days=7)
    assert exception_date.weekday() == 5
    assert not library.is_open(exception_date)
    # NOTE : the next saturday shouldn't be an exception according to this
    # exception ; BUT another exception occurred starting to 2018-12-22.
    # But this other exception is a "closed_exception" and should change the
    # behavior compare to a regular saturday
    exception_date = exception_date + timedelta(days=14)
    assert exception_date.weekday() == 5
    assert not library.is_open(exception_date)

    # CASE 3 :: Check repeatable exception date for a single date
    #   * According to library setting, each '1st augustus' is closed
    #     (from 2019); despite if '2019-08-01' is a thursday (normally open)
    exception_date = date_string_to_utc('2019-08-01')  # Thursday
    assert not library.is_open(exception_date)
    exception_date = date_string_to_utc('2022-08-01')  # Monday
    assert not library.is_open(exception_date)
    exception_date = date_string_to_utc('2018-08-01')  # Wednesday
    assert library.is_open(exception_date)
    exception_date = date_string_to_utc('2222-8-1')  # Thursday
    assert not library.is_open(exception_date)

    # CASE 4 :: Check repeatable exception range date
    #   * According to library setting, the library is closed for christmas
    #     break each year (22/12 --> 06/01)
    exception_date = date_string_to_utc('2018-12-24')  # Monday
    assert not library.is_open(exception_date)
    exception_date = date_string_to_utc('2019-01-07')  # Monday
    assert library.is_open(exception_date)
    exception_date = date_string_to_utc('2020-12-29')  # Tuesday
    assert not library.is_open(exception_date)
    exception_date = date_string_to_utc('2101-01-4')  # Tuesday
    assert not library.is_open(exception_date)

    # CASE 5 :: Check repeatable date with interval
    #   * According to library setting, each first day of the odd months is
    #     a closed day.
    exception_date = date_string_to_utc('2019-03-01')  # Friday
    assert not library.is_open(exception_date)
    exception_date = date_string_to_utc('2019-04-01')  # Monday
    assert library.is_open(exception_date)
    exception_date = date_string_to_utc('2019-05-01')  # Wednesday
    assert not library.is_open(exception_date)

    # Other tests on opening day/hour
    assert library.next_open(date=saturday).date() \
           == parser.parse('2018-12-17').date()
    assert library.next_open(date=saturday, previous=True).date() \
           == parser.parse('2018-12-14').date()

    assert library.count_open(start_date=monday, end_date=saturday) == 6
    assert library.in_working_days(
        count=6,
        date=date_string_to_utc('2018-12-10')
    ) == date_string_to_utc('2018-12-17')


def test_library_can_delete(lib_martigny):
    """Test can delete."""
    can, reasons = lib_martigny.can_delete
    assert can
    assert reasons == {}


def test_library_timezone(lib_martigny):
    """Test library timezone."""
    tz = lib_martigny.get_timezone()
    assert tz == pytz.timezone('Europe/Zurich')
