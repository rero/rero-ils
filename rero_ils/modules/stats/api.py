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

"""Stats for pricing records."""
import hashlib
from functools import partial

import arrow
from dateutil.relativedelta import relativedelta
from flask import current_app
from flask_login import current_user
from invenio_search.api import RecordsSearch

from .models import StatIdentifier, StatMetadata
from ..acq_order_lines.api import AcqOrderLinesSearch
from ..api import IlsRecord, IlsRecordsIndexer, IlsRecordsSearch
from ..documents.api import DocumentsSearch
from ..fetchers import id_fetcher
from ..items.api import ItemsSearch
from ..libraries.api import LibrariesSearch
from ..loans.logs.api import LoanOperationLog
from ..locations.api import LocationsSearch
from ..minters import id_minter
from ..patrons.api import PatronsSearch
from ..providers import Provider

# provider
StatProvider = type(
    'StatProvider',
    (Provider,),
    dict(identifier=StatIdentifier, pid_type='stat')
)
# minter
stat_id_minter = partial(id_minter, provider=StatProvider)
# fetcher
stat_id_fetcher = partial(id_fetcher, provider=StatProvider)


class StatsSearch(IlsRecordsSearch):
    """ItemTypeSearch."""

    class Meta:
        """Search only on stats index."""

        index = 'stats'
        doc_types = None
        fields = ('*',)
        facets = {}

        default_filter = None


class StatsForPricing:
    """Statistics for pricing."""

    def __init__(self, to_date=None):
        """Constructor."""
        if not to_date:
            # yesterday midnight
            self.to_date = arrow.utcnow() - relativedelta(days=1)
        else:
            self.to_date = to_date
        self.months_delta = current_app.config.get(
            'RERO_ILS_STATS_BILLING_TIMEFRAME_IN_MONTHES'
        )
        _from = (self.to_date - relativedelta(
            months=self.months_delta)).format(fmt='YYYY-MM-DDT00:00:00')
        _to = self.to_date.format(fmt='YYYY-MM-DDT23:59:59')
        self.date_range = {'gte': _from, 'lte': _to}

    def get_all_libraries(self):
        """Get all libraries in the system."""
        return list(LibrariesSearch().source(['pid', 'name', 'organisation'])
                                     .scan())

    @classmethod
    def get_stat_pid(cls, type, date_range):
        """Get pid of statistics.

        :param type: type of statistics
        :param date_range: statistics time interval
        """
        _from = date_range['from']
        _to = date_range['to']
        search = StatsSearch()\
            .filter("term", type=type)\
            .scan()

        stat_pid = list()
        for s in search:
            if 'date_range' in s and\
               'from' in s.date_range and 'to' in s.date_range:
                if s.date_range['from'] == _from and s.date_range['to'] == _to:
                    stat_pid.append(s.pid)
        if stat_pid:
            assert len(stat_pid) == 1
            return stat_pid[0]
        return

    def collect(self):
        """Compute all the statistics."""
        stats = []
        for lib in self.get_all_libraries():
            stats.append({
                'library': {
                    'pid': lib.pid,
                    'name': lib.name
                },
                'number_of_documents': self.number_of_documents(lib.pid),
                'number_of_libraries': self.number_of_libraries(
                    lib.organisation.pid),
                'number_of_librarians': self.number_of_librarians(lib.pid),
                'number_of_active_patrons': self.number_of_active_patrons(
                    lib.pid),
                'number_of_order_lines': self.number_of_order_lines(lib.pid),
                'number_of_checkouts':
                    self.number_of_circ_operations(lib.pid, 'checkout'),
                'number_of_renewals':
                    self.number_of_circ_operations(lib.pid, 'extend'),
                'number_of_satisfied_ill_request':
                    self.number_of_satisfied_ill_request(lib.pid),
                'number_of_items': self.number_of_items(lib.pid),
                'number_of_new_items': self.number_of_new_items(lib.pid),
                'number_of_deleted_items': self.number_of_deleted_items(
                    lib.pid),
                'number_of_patrons': self.number_of_patrons(
                    lib.organisation.pid),
                'number_of_new_patrons': self.number_of_patrons(
                    lib.organisation.pid),
                'number_of_checkins':
                    self.number_of_circ_operations(lib.pid, 'checkin'),
                'number_of_requests':
                    self.number_of_circ_operations(lib.pid, 'request')
            })
        return stats

    def number_of_documents(self, library_pid):
        """Number of documents linked to my library.

        point in time
        :param library_pid: string - the library to filter with
        :return: the number of matched documents
        :rtype: integer
        """
        # can be done using the facet
        return DocumentsSearch().filter(
            'term', holdings__organisation__library_pid=library_pid).count()

    def number_of_libraries(self, organisation_pid):
        """Number of libraries of the given organisation.

        point in time
        :param organisation_pid: string - the organisation to filter with
        :return: the number of matched libraries
        :rtype: integer
        """
        return LibrariesSearch().filter(
            'term', organisation__pid=organisation_pid).count()

    def number_of_librarians(self, library_pid):
        """Number of users with a librarian role.

        point in time
        :param library_pid: string - the library to filter with
        :return: the number of matched librarians
        :rtype: integer
        """
        return PatronsSearch()\
            .filter('term', roles='librarian')\
            .filter('term', libraries__pid=library_pid)\
            .count()

    def number_of_active_patrons(self, library_pid):
        """Number of patrons who did a transaction in a the past 365 days.

        :param library_pid: string - the library to filter with
        :return: the number of matched active patrons
        :rtype: integer
        """
        ptrns = set()
        _to = self.to_date.format(fmt='YYYY-MM-DDT23:59:59')
        _from = (self.to_date - relativedelta(months=12))\
            .format(fmt='YYYY-MM-DDT00:00:00')
        date_range = {'gte': _from, 'lte': _to}
        for res in RecordsSearch(index=LoanOperationLog.index_name)\
                .filter('range', date=date_range)\
                .filter('terms', loan__trigger=['checkout', 'extend'])\
                .filter('term', loan__item__library_pid=library_pid)\
                .source(['loan'])\
                .scan():
            ptrns.add(res.loan.patron.hashed_pid)

        return len(ptrns)

    def number_of_order_lines(self, library_pid):
        """Number of order lines created during the specified timeframe.

        :param library_pid: string - the library to filter with
        :return: the number of matched order lines
        :rtype: integer
        """
        return AcqOrderLinesSearch()\
            .filter('range', _created=self.date_range)\
            .filter('term', library__pid=library_pid).count()

    def number_of_circ_operations(self, library_pid, trigger):
        """Number of circulation operation  during the specified timeframe.

        :param library_pid: string - the library to filter with
        :param trigger: string - action name
        :return: the number of matched circulation operation
        :rtype: integer
        """
        return RecordsSearch(index=LoanOperationLog.index_name)\
            .filter('range', date=self.date_range)\
            .filter('term', loan__trigger=trigger)\
            .filter('term', loan__item__library_pid=library_pid)\
            .count()

    def number_of_satisfied_ill_request(self, library_pid):
        """Number of ILL requests created during the specified timeframe.

        :param library_pid: string - the library to filter with
        :return: the number of matched inter library loan request
        :rtype: integer
        """
        requests = set()
        for res in RecordsSearch(index=LoanOperationLog.index_name)\
                .filter('range', date=self.date_range)\
                .filter('term', record__type='illr')\
                .filter('term', library__pid=library_pid)\
                .filter('term', ill_request__status='validated')\
                .source(['record'])\
                .scan():
            requests.add(res.record.pid)
        return len(requests)

    # -------- optional -----------
    def number_of_items(self, library_pid):
        """Number of items linked to my library.

        point in time
        :param library_pid: string - the library to filter with
        :return: the number of matched items
        :rtype: integer
        """
        # can be done using the facet
        return ItemsSearch().filter(
            'term', library__pid=library_pid).count()

    def number_of_deleted_items(self, library_pid):
        """Number of deleted items during the specified timeframe.

        :param library_pid: string - the library to filter with
        :return: the number of matched deleted items
        :rtype: integer
        """
        return RecordsSearch(index=LoanOperationLog.index_name)\
            .filter('range', date=self.date_range)\
            .filter('term', operation='delete')\
            .filter('term', record__type='item')\
            .filter('term', library__pid=library_pid)\
            .count()

    def number_of_new_items(self, library_pid):
        """Number of new created items during the specified timeframe.

        :param library_pid: string - the library to filter with
        :return: the number of matched newly created items
        :rtype: integer
        """
        # can be done using the facet or operation logs
        return ItemsSearch()\
            .filter('range', _created=self.date_range)\
            .filter('term', library__pid=library_pid).count()

    def number_of_new_patrons(self, organisation_pid):
        """New patrons for an organisation during the specified timeframe.

        :param organisation_pid: string - the organisation to filter with
        :return: the number of matched newly created patrons
        :rtype: integer
        """
        return PatronsSearch()\
            .filter('range', _created=self.date_range)\
            .filter('term', organisation__pid=organisation_pid)\
            .count()

    def number_of_patrons(self, organisation_pid):
        """Number of users with a librarian role.

        point in time

        :param organisation_pid: string - the organisation to filter with
        :return: the number of matched patrons
        :rtype: integer
        """
        return PatronsSearch()\
            .filter('term', roles='patron')\
            .filter('term', organisation__pid=organisation_pid)\
            .count()


class StatsForLibrarian(StatsForPricing):
    """Statistics for librarian."""

    def __init__(self, to_date=None):
        """Constructor.

        :param to_date: end date of the statistics date range
        """
        if not to_date:
            # yesterday midnight
            self.to_date = arrow.utcnow() - relativedelta(days=1)
        else:
            self.to_date = to_date
        # Get statistics per month
        _from = f'{self.to_date.year}-{self.to_date.month:02d}-01T00:00:00'
        _to = self.to_date.format(fmt='YYYY-MM-DDT23:59:59')
        self.date_range = {'gte': _from, 'lte': _to}

    @classmethod
    def get_librarian_library_pids(cls):
        """Get libraries pids of librarian.

        Note: for system_librarian includes libraries of organisation.
        """
        patron_search = PatronsSearch()\
            .filter('term', user_id=current_user.id)\
            .source(['libraries', 'roles', 'organisation']).scan()
        patron_data = next(patron_search)

        library_pids = set()
        if 'librarian' in patron_data.roles:
            for library_pid in patron_data.libraries:
                library_pids.add(library_pid.pid)

        # case system_librarian: add libraries of organisation
        if 'system_librarian' in patron_data.roles:
            organisation_libraries_pid = LibrariesSearch()\
                .filter('term',
                        organisation__pid=patron_data.organisation.pid)\
                .source(['pid']).scan()
            for s in organisation_libraries_pid:
                library_pids.add(s.pid)
        return list(library_pids)

    @classmethod
    def get_librarian_libraries(cls):
        """Get libraries of librarian."""
        library_pids = cls.get_librarian_library_pids()
        return LibrariesSearch().filter('terms', pid=library_pids)\
            .source(['pid', 'name', 'organisation']).scan()

    def collect(self, **kwargs):
        """Compute statistics for librarian."""
        stats = []
        if 'libraries' in kwargs:
            libraries = kwargs.get("libraries")
        else:
            libraries = self.get_all_libraries()

        for lib in libraries:
            stats.append({
                'library': {
                    'pid': lib.pid,
                    'name': lib.name
                },
                'number_of_loans_by_transaction_library':
                    self.number_of_loans_by_transaction_library(lib.pid,
                                                                ['checkout']),
                'number_of_loans_for_items_in_library':
                    self.number_of_loans_for_items_in_library(lib.pid,
                                                              ['checkout']),
                'number_of_patrons_by_postal_code':
                    self.number_of_patrons_by_postal_code(lib.pid,
                                                          ['request',
                                                           'checkin',
                                                           'checkout']),
                'number_of_new_patrons_by_postal_code':
                    self.number_of_new_patrons_by_postal_code(lib.pid,
                                                              ['request',
                                                               'checkin',
                                                               'checkout']),
                'number_of_new_documents':
                    self.number_of_new_documents(lib.pid),
                'number_of_new_items':
                    self.number_of_new_items(lib.pid),
                'number_of_extended_items':
                    self.number_of_extended_items(lib.pid, ['extend']),
                'number_of_validated_requests':
                    self.number_of_validated_requests(lib.pid, ['validate']),
                'number_of_items_by_document_type_and_subtype':
                    self.number_of_items_by_document_type_subtype(lib.pid),
                'number_of_new_items_by_location':
                    self.number_of_new_items_by_location(lib.pid)
            })
        return stats

    def _get_locations_pid(self, library_pid):
        """Locations pid for given library.

        :param library_pid: string - the library to filter with
        :return: list of pid locations
        :rtype: list
        """
        locations = LocationsSearch()\
            .filter('term', library__pid=library_pid).source('pid').scan()
        return [location.pid for location in locations]

    def _get_location_code_name(self, location_pid):
        """Location code and name.

        :param location_pid: string - the location to filter with
        :return: concatenated code and name of location
        :rtype: string
        """
        location_search = LocationsSearch()\
            .filter('term', pid=location_pid)\
            .source(['code', 'name']).scan()
        location = next(location_search)
        return f'{location.code} - {location.name}'

    def number_of_loans_by_transaction_library(self, library_pid, trigger):
        """Number of circulation operation during the specified timeframe.

        Number of loans of items when transaction location is equal to
        any of the library locations
        :param library_pid: string - the library to filter with
        :param trigger: string - action name (checkout)
        :return: the number of matched circulation operation
        :rtype: integer
        """
        location_pids = self._get_locations_pid(library_pid)

        return RecordsSearch(index=LoanOperationLog.index_name)\
            .filter('range', date=self.date_range)\
            .filter('terms', loan__trigger=trigger)\
            .filter('terms', loan__transaction_location__pid=location_pids)\
            .count()

    def number_of_loans_for_items_in_library(self, library_pid, trigger):
        """Number of circulation operation during the specified timeframe.

        Number of loans of items per library when the item is owned by
        the library
        :param library_pid: string - the library to filter with
        :param trigger: string - action name (checkout)
        :return: the number of matched circulation operation
        :rtype: integer
        """
        return RecordsSearch(index=LoanOperationLog.index_name)\
            .filter('range', date=self.date_range)\
            .filter('terms', loan__trigger=trigger)\
            .filter('term', loan__item__library_pid=library_pid)\
            .count()

    def number_of_patrons_by_postal_code(self, library_pid, trigger):
        """Number of circulation operation during the specified timeframe.

        Number of patrons per library and CAP when transaction location
        is equal to any of the library locations
        :param library_pid: string - the library to filter with
        :param trigger: string - action name (request, checkin, checkout)
        :return: the number of matched circulation operation
        :rtype: dict
        """
        location_pids = self._get_locations_pid(library_pid)

        search = RecordsSearch(index=LoanOperationLog.index_name)\
            .filter('range', date=self.date_range)\
            .filter('terms', loan__trigger=trigger)\
            .filter('terms', loan__transaction_location__pid=location_pids)\
            .scan()

        stats = {}
        patron_pids = set()
        # Main postal code from user profile
        for s in search:
            patron_pid = s.loan.patron.hashed_pid
            if 'postal_code' not in s.loan.patron or\
                    not s.loan.patron.postal_code:
                postal_code = 'unknown'
            else:
                postal_code = s.loan.patron.postal_code

            if postal_code not in stats:
                stats[postal_code] = 1
            else:
                if patron_pid not in patron_pids:
                    stats[postal_code] += 1
            patron_pids.add(patron_pid)
        return stats

    def number_of_new_patrons_by_postal_code(self, library_pid, trigger):
        """Number of circulation operation during the specified timeframe.

        Number of new patrons per library and CAP when transaction location
        is equal to any of the library locations
        :param library_pid: string - the library to filter with
        :param trigger: string - action name (request, checkin, checkout)
        :return: the number of matched circulation operation
        :rtype: dict
        """
        location_pids = self._get_locations_pid(library_pid)

        search = RecordsSearch(index=LoanOperationLog.index_name)\
            .filter('range', date=self.date_range)\
            .filter('terms', loan__trigger=trigger)\
            .filter('terms', loan__transaction_location__pid=location_pids)\
            .scan()

        # Get new patrons in date range and hash the pids
        search_patron = PatronsSearch()\
            .filter("range", _created=self.date_range)\
            .source('pid').scan()
        new_patron_pids = set()
        for p in search_patron:
            hashed_pid = hashlib.md5(p.pid.encode()).hexdigest()
            new_patron_pids.add(hashed_pid)

        stats = {}
        patron_pids = set()
        # Main postal code from user profile
        for s in search:
            patron_pid = s.loan.patron.hashed_pid
            if patron_pid in new_patron_pids:
                if 'postal_code' not in s.loan.patron or\
                        not s.loan.patron.postal_code:
                    postal_code = 'unknown'
                else:
                    postal_code = s.loan.patron.postal_code

                if postal_code not in stats:
                    stats[postal_code] = 1
                else:
                    if patron_pid not in patron_pids:
                        stats[postal_code] += 1
                patron_pids.add(patron_pid)

        return stats

    def number_of_new_documents(self, library_pid):
        """Number of new documents per library for given time interval.

        :param library_pid: string - the library to filter with
        :return: the number of matched documents
        :rtype: integer
        """
        return RecordsSearch(index=LoanOperationLog.index_name)\
            .filter('range', date=self.date_range)\
            .filter('term', operation='create')\
            .filter('term', record__type='doc')\
            .filter('term', library__value=library_pid)\
            .count()

    def number_of_extended_items(self, library_pid, trigger):
        """Number of items with loan extended.

        Number of items with loan extended per library for given time interval
        :param library_pid: string - the library to filter with
        :param trigger: string - action name extend
        :return: the number of matched documents
        :rtype: integer
        """
        return RecordsSearch(index=LoanOperationLog.index_name)\
            .filter('range', date=self.date_range)\
            .filter('terms', loan__trigger=trigger)\
            .filter('term', loan__item__library_pid=library_pid)\
            .count()

    def number_of_validated_requests(self, library_pid, trigger):
        """Number of validated requests.

        Number of validated requests per library for given time interval
        Match is done on the library of the librarian.
        Note: trigger is 'validate' and not 'validate_request'
        :param library_pid: string - the library to filter with
        :param trigger: string - action name validate
        :return: the number of matched documents
        :rtype: integer
        """
        return RecordsSearch(index=LoanOperationLog.index_name)\
            .filter('range', date=self.date_range)\
            .filter('terms', loan__trigger=trigger)\
            .filter('term', library__value=library_pid)\
            .count()

    def number_of_new_items_by_location(self, library_pid):
        """Number of new items per library by location.

        Note: items created and then deleted during the time interval
        are not included.
        :param library_pid: string - the library to filter with
        :return: the number of matched documents
        :rtype: dict
        """
        search = ItemsSearch()[0:0]\
            .filter('range', _created=self.date_range)\
            .filter('term', library__pid=library_pid)\
            .source('location.pid')
        search.aggs.bucket('location_pid', 'terms', field='location.pid',
                           size=10000)
        res = search.execute()
        stats = {}
        for bucket in res.aggregations.location_pid.buckets:
            location_code_name = self._get_location_code_name(bucket.key)
            stats[location_code_name] = bucket.doc_count
        return stats

    def number_of_items_by_document_type_subtype(self, library_pid):
        """Number of items per library by document type and sub-type.

        Note: if item has more than one doc type/subtype the item is counted
        multiple times
        :param library_pid: string - the library to filter with
        :return: the number of matched documents
        :rtype: dict
        """
        search = ItemsSearch()[0:0]\
            .filter('range', _created={'lte': self.date_range['lte']})\
            .filter('term', library__pid=library_pid)\
            .source('document.document_type')
        search.aggs\
              .bucket('main_type', 'terms',
                      field='document.document_type.main_type', size=10000)
        search.aggs\
              .bucket('subtype', 'terms',
                      field='document.document_type.subtype', size=10000)
        res = search.execute()
        stats = {}
        for bucket in res.aggregations.main_type.buckets:
            stats[bucket.key] = bucket.doc_count
        for bucket in res.aggregations.subtype.buckets:
            stats[bucket.key] = bucket.doc_count
        return stats


class Stat(IlsRecord):
    """ItemType class."""

    minter = stat_id_minter
    fetcher = stat_id_fetcher
    provider = StatProvider
    model_cls = StatMetadata

    def update(self, data, commit=True, dbcommit=False, reindex=False):
        """Update data for record."""
        super().update(data, commit, dbcommit, reindex)
        return self


class StatsIndexer(IlsRecordsIndexer):
    """Indexing stats in Elasticsearch."""

    record_cls = Stat

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(record_id_iterator, doc_type='stat')
