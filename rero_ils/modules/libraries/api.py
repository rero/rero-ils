# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
# Copyright (C) 2019-2023 UCLouvain
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

"""API for manipulating `Library` resources."""

from datetime import datetime, timedelta
from functools import partial

import pytz
from dateutil import parser
from dateutil.rrule import FREQNAMES, rrule
from elasticsearch_dsl import Q
from flask_babel import gettext as _

from rero_ils.modules.api import IlsRecord, IlsRecordsIndexer, IlsRecordsSearch
from rero_ils.modules.fetchers import id_fetcher
from rero_ils.modules.locations.api import LocationsSearch
from rero_ils.modules.minters import id_minter
from rero_ils.modules.providers import Provider
from rero_ils.modules.stats_cfg.api import StatsConfigurationSearch
from rero_ils.modules.users.models import UserRole
from rero_ils.modules.utils import date_string_to_utc, \
    extracted_data_from_ref, sorted_pids, strtotime

from .exceptions import LibraryNeverOpen
from .extensions import LibraryCalendarChangesExtension
from .models import LibraryAddressType, LibraryIdentifier, LibraryMetadata

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


class LibrariesSearch(IlsRecordsSearch):
    """Libraries search."""

    class Meta():
        """Meta class."""

        index = 'libraries'
        doc_types = None
        fields = ('*', )
        facets = {}

        default_filter = None

    def by_organisation_pid(self, organisation_pid):
        """Build a search to get hits related to an organisation pid.

        :param organisation_pid: string - the organisation pid to filter with
        :returns: An ElasticSearch query to get hits related the entity.
        :rtype: `elasticsearch_dsl.Search`
        """
        return self.filter('term', organisation__pid=organisation_pid)


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

    _extensions = [
        LibraryCalendarChangesExtension(['opening_hours', 'exception_dates'])
    ]

    def extended_validation(self, **kwargs):
        """Add additional record validation.

        :return: reason for validation failure, otherwise True
        """
        for exception_date in self.get('exception_dates', []):
            if exception_date['is_open'] and not exception_date.get('times'):
                return _('Opening times must be specified for an open '
                         'exception date.')
        return True

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
        return extracted_data_from_ref(self['organisation'], data='record')

    def get_address(self, address_type):
        """Get informations about an address type.

        :param address_type: the type of address.
        :return a dict with all necessary address data.
        """
        if address_type == LibraryAddressType.MAIN_ADDRESS:
            return self.get('address')
        else:
            return self.get('acquisition_settings', {}) \
                .get(f'{address_type}_informations', {}).get('address')

    def get_email(self, notification_type):
        """Get the email corresponding to the given notification type.

        :param notification_type: the notification type.
        :return: the email corresponding to the notification type if found
        :rtype: string | None
        """
        # notification_settings is not a required field.
        if notification_type:
            for setting in self.get('notification_settings', []):
                if setting['type'] == notification_type:
                    return setting['email']

    def _pickup_location_query(self):
        """Search the location index for pickup locations."""
        return LocationsSearch() \
            .filter('term', library__pid=self.pid) \
            .filter('term', is_pickup=True) \
            .source(['pid']) \
            .scan()

    def location_pids(self):
        """Return a generator of ES Hits of all pids of library locations."""
        return LocationsSearch() \
            .filter('term', library__pid=self.pid) \
            .source(['pid']) \
            .scan()

    def get_pickup_locations_pids(self):
        """Returns libraries all pickup locations pids."""
        for location in self._pickup_location_query():
            yield location.pid

    def get_pickup_location_pid(self):
        """Returns one picup location pid for a library."""
        try:
            return next(self._pickup_location_query()).pid
        except StopIteration:
            return None

    def get_transaction_location_pid(self):
        """Returns one pickup or one transaction location pid for a library."""
        try:
            return next(self._pickup_location_query()).pid
        except StopIteration:
            return next(self.location_pids()).pid

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

    def _has_is_open(self):
        """Test if library has opening days in the future."""
        if opening_hours := self.get('opening_hours'):
            for opening_hour in opening_hours:
                if opening_hour['is_open']:
                    return True
        current_timestamp = datetime.now(pytz.utc)
        for exception_date in filter(
            lambda d: d['is_open'],
            self.get('exception_dates', [])
        ):
            start_date = date_string_to_utc(exception_date['start_date'])
            # avoid next_open infinite loop if an open exception date is
            # in the past
            if start_date > current_timestamp:
                return True
        return False

    def _get_exceptions_matching_date(self, date_to_check, day_only=False):
        """Get all exception matching a given date."""
        for exception in self.get('exception_dates', []):
            # Get the start date and the gap (in days) between start date and
            # end date. If no end_date are supplied, the gap will be 0.
            start_date = date_string_to_utc(exception['start_date'])
            end_date = start_date
            day_gap = 0
            if exception.get('end_date'):
                end_date = date_string_to_utc(exception.get('end_date'))
                day_gap = (end_date - start_date).days

            # If the exception is repeatable, then the start_date should be the
            # nearest date (lower or equal than date_to_check) related to the
            # repeat period/interval definition. To know that, we need to know
            # all exception dates possible (form exception start_date to
            # date_to_check) and get only the last one.
            if exception.get('repeat'):
                period = exception['repeat']['period'].upper()
                exception_dates = rrule(
                    freq=FREQNAMES.index(period),
                    until=date_to_check,
                    interval=exception['repeat']['interval'],
                    dtstart=start_date
                )
                for start_date in exception_dates:
                    pass
                end_date = start_date + timedelta(days=day_gap)

            # Now, check if exception is matching for the date_to_check
            # If exception defined times, we need to check if the date_to_check
            # is includes into theses time intervals (only if `day_only` method
            # argument is set)
            if start_date.date() <= date_to_check.date() <= end_date.date():
                if exception.get('times') and not day_only:
                    times = exception.get('times')
                    if self._is_betweentimes(date_to_check.time(), times):
                        yield exception
                else:
                    yield exception

    def is_open(self, date=None, day_only=False):
        """Test library is open."""
        date = date or datetime.now(pytz.utc)
        is_open = False
        rule_hours = []

        # First, change date to be aware and with timezone.
        if isinstance(date, str):
            date = date_string_to_utc(date)
        if isinstance(date, datetime) and date.tzinfo is None:
            date = date.replace(tzinfo=pytz.utc)

        # STEP 1 :: check about regular rules
        #   Each library could define if a specific weekday is open or closed.
        #   Check into this weekday array if the day is open/closed. If the
        #   searched weekday isn't defined the default value is closed
        #
        #   If the find rule defined open time periods, check if date_to_check
        #   is into one of these periods (depending on `day_only` method
        #   argument).
        day_name = date.strftime('%A').lower()
        regular_rule = [
            rule for rule in self.get('opening_hours', [])
            if rule['day'] == day_name
        ]
        if regular_rule:
            is_open = regular_rule[0].get('is_open', False)
            rule_hours = regular_rule[0].get('times', [])

        if is_open and not day_only:
            is_open = self._is_betweentimes(date.time(), rule_hours)

        # STEP 2 :: test each exception
        #   Each library can define a set of exception dates. These exceptions
        #   could be repeatable for a specific interval. Check is some
        #   exceptions are relevant related to date_to_check and if these
        #   exceptions changed the behavior of regular rules.
        #
        #   Each exception can define open time periods, check if
        #   date_to_check is into one of these periods (depending on `day_only`
        #   method argument)
        for exception in self._get_exceptions_matching_date(date, day_only):
            if is_open != exception['is_open']:
                is_open = not is_open

        return is_open

    def _get_opening_hour_by_day(self, day_name):
        """Get the library opening hour for a specific day."""
        day_name = day_name.lower()
        days = [
            day for day in self.get('opening_hours', [])
            if day['day'] == day_name and day['is_open']
        ]
        if days and days[0]['times']:
            return days[0]['times'][0]['start_time']

    def next_open(self, date=None, previous=False, ensure=False):
        """Get next open day."""
        date = date or datetime.now(pytz.utc)
        if not self._has_is_open():
            raise LibraryNeverOpen(
                f'No open days found for library (pid: {self.pid})'
                )
        if isinstance(date, str):
            date = parser.parse(date)
        add_day = -1 if previous else 1
        date += timedelta(days=add_day)
        while not self.is_open(date=date, day_only=True):
            date += timedelta(days=add_day)
        if not ensure:
            return date
        opening_hour = self._get_opening_hour_by_day(date.strftime('%A'))
        time = [int(part) for part in opening_hour.split(':')]
        return date.replace(
            hour=time[0],
            minute=time[1],
            second=0,
            microsecond=0
        )

    def get_open_days(self, start_date=None, end_date=None):
        """Get all open days between date interval."""
        start_date = start_date or datetime.now(pytz.utc)
        end_date = end_date or datetime.now(pytz.utc)
        if isinstance(start_date, str):
            start_date = date_string_to_utc(start_date)
        if isinstance(end_date, str):
            end_date = date_string_to_utc(end_date)

        dates = []
        end_date += timedelta(days=1)
        while end_date > start_date:
            if self.is_open(date=start_date, day_only=True):
                dates.append(start_date)
            start_date += timedelta(days=1)
        return dates

    def count_open(self, start_date=None, end_date=None):
        """Get number of open day between date interval."""
        start_date = start_date or datetime.now(pytz.utc)
        end_date = end_date or datetime.now(pytz.utc)
        return len(self.get_open_days(start_date, end_date))

    def in_working_days(self, count, date=None):
        """Get date for given working days."""
        date = date or datetime.now(pytz.utc)
        counting = 1
        if isinstance(date, str):
            date = date_string_to_utc(date)
        while counting <= count:
            counting += 1
            date = self.next_open(date=date)
        return date

    def get_links_to_me(self, get_pids=False):
        """Record links.

        :param get_pids: if True list of linked pids
                         if False count of linked records
        """
        from rero_ils.modules.acquisition.acq_receipts.api import \
            AcqReceiptsSearch
        from rero_ils.modules.patrons.api import PatronsSearch
        links = {}
        stat_cfg_query = StatsConfigurationSearch()\
            .filter(
                Q('term', library__pid=self.pid) |
                Q('term', filter_by_libraries__pid=self.pid)
            )
        location_query = LocationsSearch() \
            .filter('term', library__pid=self.pid)
        patron_query = PatronsSearch() \
            .filter('term', libraries__pid=self.pid) \
            .filter('terms', roles=UserRole.PROFESSIONAL_ROLES)
        receipt_query = AcqReceiptsSearch() \
            .filter('term', library__pid=self.pid)
        if get_pids:
            locations = sorted_pids(location_query)
            librarians = sorted_pids(patron_query)
            receipts = sorted_pids(receipt_query)
            stats_cfg = sorted_pids(stat_cfg_query)
        else:
            locations = location_query.count()
            librarians = patron_query.count()
            receipts = receipt_query.count()
            stats_cfg = stat_cfg_query.count()
        if locations:
            links['locations'] = locations
        if librarians:
            links['patrons'] = librarians
        if receipts:
            links['acq_receipts'] = receipts
        if stats_cfg:
            links['stats_cfg'] = stats_cfg
        return links

    def reasons_not_to_delete(self):
        """Get reasons not to delete record."""
        cannot_delete = {}
        if links := self.get_links_to_me():
            cannot_delete['links'] = links
        return cannot_delete

    def get_timezone(self):
        """Get library timezone."""
        # TODO: get timezone regarding Library address.
        # TODO: Use BABEL_DEFAULT_TIMEZONE by default
        return pytz.timezone('Europe/Zurich')

    def get_online_harvested_source_url(self, source):
        """Get online harvested source url."""
        for harvested_source in self.get('online_harvested_source', []):
            if harvested_source.get('source') == source:
                return harvested_source['url']


class LibrariesIndexer(IlsRecordsIndexer):
    """Holdings indexing class."""

    record_cls = Library

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(record_id_iterator, doc_type='lib')
