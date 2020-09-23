# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
# Copyright (C) 2020 UCLouvain
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

"""API for manipulating libraries."""

from datetime import datetime, timedelta
from functools import partial

import pytz
from dateutil import parser
from dateutil.rrule import FREQNAMES, rrule

from .models import LibraryIdentifier, LibraryMetadata
from ..api import IlsRecord, IlsRecordsIndexer, IlsRecordsSearch
from ..fetchers import id_fetcher
from ..locations.api import LocationsSearch
from ..minters import id_minter
from ..providers import Provider
from ..utils import date_string_to_utc, strtotime

# provider
LibraryProvider = type(
    'LibraryProvider',
    (Provider,),
    dict(identifier=LibraryIdentifier, pid_type='lib')
)
# minter
library_id_minter = partial(id_minter, provider=LibraryProvider)
# fetcher
library_id_fetcher = partial(id_fetcher, provider=LibraryProvider)


# define Python user-defined exceptions
class LibraryNeverOpen(Exception):
    """Raised when the library has no open days."""


class LibrariesSearch(IlsRecordsSearch):
    """Libraries search."""

    class Meta():
        """Meta class."""

        index = 'libraries'
        doc_types = None
        fields = ('*', )
        facets = {}

        default_filter = None


class Library(IlsRecord):
    """Library class."""

    minter = library_id_minter
    fetcher = library_id_fetcher
    provider = LibraryProvider
    model_cls = LibraryMetadata
    pids_exist_check = {
        'required': {
            'org': 'organisation'
        }
    }

    @property
    def online_location(self):
        """Get the online location."""
        result = LocationsSearch()\
            .filter('term', is_online=True)\
            .filter('term', library__pid=self.pid)\
            .source(['pid']).scan()
        try:
            return next(result).pid
        except StopIteration:
            return None

    def get_organisation(self):
        """Get Organisation."""
        from ..organisations.api import Organisation
        return Organisation.get_record_by_pid(self.organisation_pid)

    def get_pickup_location_pid(self):
        """Returns libraries first pickup location."""
        results = LocationsSearch().filter(
            'term', library__pid=self.pid).filter(
                'term', is_pickup=True).source(['pid']).scan()
        try:
            return next(results).pid
        except StopIteration:
            return None

    def _is_betweentimes(self, time_to_test, times):
        """Test if time is between times."""
        times_open = False
        for time_given in times:
            start_time = strtotime(time_given['start_time'])
            end_time = strtotime(time_given['end_time'])

            if time_to_test.hour == time_to_test.minute == \
                    time_to_test.second == 0:
                # case when library is open or close few hours per day
                times_open = times_open or end_time > start_time
            else:
                times_open = times_open or ((time_to_test >= start_time) and
                                            (time_to_test <= end_time))
        return times_open

    def _is_in_period(self, datetime_to_test, exception_date, day_only):
        """Test if date is period."""
        start_date = exception_date['start_date']
        if isinstance(exception_date['start_date'], str):
            start_date = date_string_to_utc(start_date)
        end_date = exception_date.get('end_date')
        if end_date:
            if isinstance(end_date, str):
                end_date = date_string_to_utc(end_date)
            is_in_period = (
                datetime_to_test.date() - start_date.date()
            ).days >= 0
            is_in_period = is_in_period and (
                end_date.date() - datetime_to_test.date()
            ).days >= 0
            return True, is_in_period
        if not end_date and day_only:
            # case when exception if full day
            if datetime_to_test.date() == start_date.date():
                return False, True
        return False, False

    def _is_in_repeat(self, datetime_to_test, start_date, repeat):
        """Test repeating date."""
        if repeat:
            period = repeat['period'].upper()
            interval = repeat['interval']
            datelist_to_test = list(
                rrule(
                    freq=FREQNAMES.index(period),
                    until=datetime_to_test,
                    interval=interval,
                    dtstart=start_date
                )
            )
            for date in datelist_to_test:
                if date.date() == datetime_to_test.date():
                    return True
        return datetime_to_test.date() == start_date

    def _has_exception(self, _open, date, exception_dates,
                       day_only=False):
        """Test the day has an exception."""
        exception = _open
        for exception_date in exception_dates:
            if isinstance(exception_date['start_date'], str):
                start_date = date_string_to_utc(exception_date['start_date'])
            repeat = exception_date.get('repeat')
            if _open:
                # test for closed exceptions
                if not exception_date['is_open']:
                    has_period, is_in_period = self._is_in_period(
                        date,
                        exception_date,
                        day_only
                    )
                    if has_period and is_in_period:
                        exception = False
                    if not has_period and is_in_period:
                        # case when exception if full day
                        exception = exception_date['is_open']
                    if self._is_in_repeat(date, start_date, repeat):
                        exception = False
                    # we found a closing exception
                    if not exception:
                        return False
            else:
                # test for opened exceptions
                if exception_date['is_open']:
                    if self._is_in_repeat(date, start_date, repeat):
                        exception = True
                    if not exception and not day_only:
                        exception = self._is_betweentimes(
                            date.time(),
                            exception_date.get('times', [])
                        )
                    return exception
        return exception

    def _has_is_open(self):
        """Test if library has opening days."""
        opening_hours = self.get('opening_hours')
        if opening_hours:
            for opening_hour in opening_hours:
                if opening_hour['is_open']:
                    return True
        exception_dates = self.get('exception_dates')
        if exception_dates:
            for exception_date in exception_dates:
                if exception_date['is_open']:
                    return True
        return False

    def is_open(self, date=datetime.now(pytz.utc), day_only=False):
        """Test library is open."""
        _open = False

        # Change date to be aware and with timezone.
        if isinstance(date, str):
            date = date_string_to_utc(date)
        if isinstance(date, datetime):
            if date.tzinfo is None:
                date = date.replace(tzinfo=pytz.utc)
        day_name = date.strftime("%A").lower()
        for opening_hour in self['opening_hours']:
            if day_name == opening_hour['day']:
                _open = opening_hour['is_open']
                hours = opening_hour.get('times', [])
                break
        times_open = _open
        if _open and not day_only:
            times_open = self._is_betweentimes(date.time(), hours)
        # test the exceptions
        exception_dates = self.get('exception_dates')
        if exception_dates:
            exception = self._has_exception(
                _open=times_open,
                date=date,
                exception_dates=exception_dates,
                day_only=day_only
            )
            if exception != times_open:
                times_open = not times_open
        return times_open

    def next_open(self, date=datetime.now(pytz.utc), previous=False):
        """Get next open day."""
        if not self._has_is_open():
            raise LibraryNeverOpen
        if isinstance(date, str):
            date = parser.parse(date)
        add_day = 1
        if previous:
            add_day = -1
        date += timedelta(days=add_day)
        while not self.is_open(date=date, day_only=True):
            date += timedelta(days=add_day)
        return date

    def count_open(self, start_date=datetime.now(pytz.utc),
                   end_date=datetime.now(pytz.utc), day_only=False):
        """Get next open day."""
        if isinstance(start_date, str):
            start_date = date_string_to_utc(start_date)
        if isinstance(end_date, str):
            end_date = date_string_to_utc(end_date)

        count = 0
        end_date += timedelta(days=1)
        while end_date > start_date:
            if self.is_open(date=start_date, day_only=True):
                count += 1
            start_date += timedelta(days=1)
        return count

    def in_working_days(self, count, date=datetime.now(pytz.utc)):
        """Get date for given working days."""
        counting = 1
        if isinstance(date, str):
            date = date_string_to_utc(date)
        while counting <= count:
            counting += 1
            date = self.next_open(date=date)
        return date

    def get_number_of_librarians(self):
        """Get number of librarians."""
        from ..patrons.api import PatronsSearch
        results = PatronsSearch().filter(
            'term', library__pid=self.pid).filter(
                'term', roles='librarian').source().count()
        return results

    def get_number_of_locations(self):
        """Get number of locations."""
        results = LocationsSearch().filter(
            'term', library__pid=self.pid).source().count()
        return results

    def get_links_to_me(self):
        """Get number of links."""
        links = {}
        locations = self.get_number_of_locations()
        if locations:
            links['locations'] = locations
        librarians = self.get_number_of_librarians()
        if librarians:
            links['patrons'] = librarians
        return links

    def reasons_not_to_delete(self):
        """Get reasons not to delete record."""
        cannot_delete = {}
        links = self.get_links_to_me()
        if links:
            cannot_delete['links'] = links
        return cannot_delete

    def get_timezone(self):
        """Get library timezone."""
        # TODO: get timezone regarding Library address.
        # TODO: Use BABEL_DEFAULT_TIMEZONE by default
        default = pytz.timezone('Europe/Zurich')
        return default


class LibrariesIndexer(IlsRecordsIndexer):
    """Holdings indexing class."""

    record_cls = Library

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super(LibrariesIndexer, self).bulk_index(record_id_iterator,
                                                 doc_type='lib')
