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

from rero_ils.modules.libraries.api import LibrariesSearch, Library
from rero_ils.modules.libraries.api import library_id_fetcher as fetcher
from rero_ils.modules.libraries.models import LibraryAddressType
from rero_ils.modules.notifications.models import NotificationType
from rero_ils.modules.utils import date_string_to_utc


def test_classes_api_methods(org_martigny, lib_martigny):
    """Test some specific methods related to `Library` resources."""
    org = org_martigny
    lib = lib_martigny

    # TEST : LibrariesSearch::get_libraries_by_organisation_pid
    fields = ['name']
    hits = list(
        LibrariesSearch()
        .get_libraries_by_organisation_pid(org.pid, fields=fields)
    )
    assert len(hits) == 1
    assert 'name' in hits[0]
    assert 'code' not in hits[0]

    # TEST :: Library.get_organisation
    assert lib.get_organisation() == org


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
    orginal_date = datetime.strptime('2020/08/17', '%Y/%m/%d')  # random date
    for day_idx in range(0, 5):
        test_date = next_weekday(orginal_date, day_idx)
        test_date = test_date.replace(hour=6, minute=0)
        assert not library.is_open(test_date)
        test_date = test_date.replace(hour=12)
        assert library.is_open(test_date)
    test_date = next_weekday(orginal_date, 5)
    assert not library.is_open(test_date)
    test_date = next_weekday(orginal_date, 6)
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


def test_library_get_address(lib_martigny, lib_saxon):
    """Get information about a library address."""
    lib = lib_martigny
    address = lib.get_address(LibraryAddressType.MAIN_ADDRESS)
    assert address == lib.get('address')
    address = lib.get_address(LibraryAddressType.SHIPPING_ADDRESS)
    assert address['country'] == 'sz'  # translated at 'Suisse (sz)'
    address = lib.get_address(LibraryAddressType.BILLING_ADDRESS)
    assert address['country'] == 'be'
    address = lib.get_address('dummy_type')
    assert address is None

    lib = lib_saxon
    address = lib.get_address(LibraryAddressType.BILLING_ADDRESS)
    assert address is None


def test_library_get_email(lib_martigny):
    """Test the get_email function about a library."""

    def notification_email(library, notif_type):
        for setting in library.get('notification_settings', []):
            if setting.get('type') == notif_type:
                return setting.get('email')

    assert lib_martigny.get_email(NotificationType.RECALL) == \
        notification_email(lib_martigny, NotificationType.RECALL)
    assert not lib_martigny.get_email('dummy_notification_type')


def test_library_get_links_to_me(
    lib_martigny,
    loc_public_martigny,
    loc_public_sion
):
    """Test library links."""
    assert lib_martigny.get_links_to_me() == {'locations': 1}
    assert lib_martigny.get_links_to_me(get_pids=True) == {
        'locations': ['loc1']
    }
