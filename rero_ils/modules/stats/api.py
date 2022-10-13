# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
# Copyright (C) 2019-2022 UCLouvain
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
from datetime import datetime
from functools import partial

import arrow
import ciso8601
from dateutil.relativedelta import relativedelta
from elasticsearch_dsl import Q
from flask import current_app
from invenio_search.api import RecordsSearch
from webargs import ValidationError

from rero_ils.modules.acquisition.acq_order_lines.api import \
    AcqOrderLinesSearch
from rero_ils.modules.api import IlsRecord, IlsRecordsIndexer, IlsRecordsSearch
from rero_ils.modules.documents.api import DocumentsSearch
from rero_ils.modules.fetchers import id_fetcher
from rero_ils.modules.holdings.api import HoldingsSearch
from rero_ils.modules.ill_requests.api import ILLRequestsSearch
from rero_ils.modules.ill_requests.models import ILLRequestStatus
from rero_ils.modules.items.api import ItemsSearch
from rero_ils.modules.items.models import ItemCirculationAction
from rero_ils.modules.libraries.api import LibrariesSearch, Library
from rero_ils.modules.loans.logs.api import LoanOperationLog
from rero_ils.modules.locations.api import Location, LocationsSearch
from rero_ils.modules.minters import id_minter
from rero_ils.modules.organisations.api import Organisation
from rero_ils.modules.patrons.api import PatronsSearch
from rero_ils.modules.providers import Provider
from rero_ils.modules.stats.exceptions import NotActiveStatConfigException, \
    StatReportDistributionsValidatorException
from rero_ils.modules.stats.extensions import StatisticsDumperExtension
from rero_ils.modules.stats.models import StatDistributions, StatIdentifier, \
    StatIndicators, StatMetadata
from rero_ils.modules.stats_cfg.api import StatConfiguration
from rero_ils.modules.users.models import UserRole
from rero_ils.modules.utils import extracted_data_from_ref

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


class Stat(IlsRecord):
    """Stat class."""

    minter = stat_id_minter
    fetcher = stat_id_fetcher
    provider = StatProvider
    model_cls = StatMetadata

    _extensions = [
        StatisticsDumperExtension()
    ]

    def update(self, data, commit=True, dbcommit=False, reindex=False):
        """Update data for record."""
        super().update(data, commit, dbcommit, reindex)
        return self


class StatsForPricing:
    """Statistics for pricing."""

    def __init__(self, to_date=None):
        """Constructor."""
        self.to_date = to_date or arrow.utcnow() - relativedelta(days=1)
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
                    self.number_of_circ_operations(
                        lib.pid, ItemCirculationAction.CHECKOUT),
                'number_of_renewals':
                    self.number_of_circ_operations(
                        lib.pid, ItemCirculationAction.EXTEND),
                'number_of_satisfied_ill_request':
                    self.number_of_satisfied_ill_request(
                        lib.pid,
                        [ILLRequestStatus.PENDING, ILLRequestStatus.VALIDATED,
                         ILLRequestStatus.CLOSED]),
                'number_of_items': self.number_of_items(lib.pid),
                'number_of_new_items': self.number_of_new_items(lib.pid),
                'number_of_deleted_items': self.number_of_deleted_items(
                    lib.pid),
                'number_of_patrons': self.number_of_patrons(
                    lib.organisation.pid),
                'number_of_new_patrons': self.number_of_patrons(
                    lib.organisation.pid),
                'number_of_checkins':
                    self.number_of_circ_operations(
                        lib.pid,  ItemCirculationAction.CHECKIN),
                'number_of_requests':
                    self.number_of_circ_operations(
                        lib.pid,  ItemCirculationAction.REQUEST)
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
            .filter('terms', roles=UserRole.PROFESSIONAL_ROLES)\
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
                .filter(
                    'terms',
                    loan__trigger=[ItemCirculationAction.CHECKOUT,
                                   ItemCirculationAction.EXTEND])\
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

    def number_of_satisfied_ill_request(self, library_pid, status):
        """Number of ILL requests created during the specified timeframe.

        :param library_pid: string - the library to filter with
        :param status: list of status to filter with
        :return: the number of matched inter library loan request
        :rtype: integer
        """
        query = RecordsSearch(index=LoanOperationLog.index_name)\
            .filter('term', record__type='illr')\
            .filter('term', operation='create')\
            .filter('range', _created=self.date_range)\
            .filter('term', ill_request__library_pid=library_pid)\
            .filter('terms', ill_request__status=status)
        return query.count()

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
    """Statistics for librarian.

    TODO: the type of the statistic should be changed from
          librarian to library.
    """

    def __init__(self, to_date=None):
        """Constructor.

        :param to_date: end date of the statistics date range
        """
        self.to_date = to_date or arrow.utcnow() - relativedelta(days=1)
        # Get statistics per month
        _from = f'{self.to_date.year}-{self.to_date.month:02d}-01T00:00:00'
        _to = self.to_date.format(fmt='YYYY-MM-DDT23:59:59')
        self.date_range = {'gte': _from, 'lte': _to}

    def collect(self):
        """Compute statistics for librarian."""
        stats = []
        libraries = self.get_all_libraries()
        libraries_map = {lib.pid: lib.name for lib in libraries}

        for lib in libraries:
            stats.append({
                'library': {
                    'pid': lib.pid,
                    'name': lib.name
                },
                'checkouts_for_transaction_library':
                    self.checkouts_for_transaction_library(
                        lib.pid,
                        [ItemCirculationAction.CHECKOUT]),
                'checkouts_for_owning_library':
                    self.checkouts_for_owning_library(
                        lib.pid,
                        [ItemCirculationAction.CHECKOUT]),
                'active_patrons_by_postal_code':
                    self.active_patrons_by_postal_code(
                        lib.pid,
                        [ItemCirculationAction.REQUEST,
                         ItemCirculationAction.CHECKIN,
                         ItemCirculationAction.CHECKOUT]),
                'new_active_patrons_by_postal_code':
                    self.new_active_patrons_by_postal_code(
                        lib.pid,
                        [ItemCirculationAction.REQUEST,
                         ItemCirculationAction.CHECKIN,
                         ItemCirculationAction.CHECKOUT]),
                'new_documents':
                    self.new_documents(lib.pid),
                'new_items':
                    self.number_of_new_items(lib.pid),
                'renewals':
                    self.renewals(lib.pid, [ItemCirculationAction.EXTEND]),
                'validated_requests':
                    self.validated_requests(lib.pid, ['validate']),
                'items_by_document_type_and_subtype':
                    self.items_by_document_type_and_subtype(lib.pid),
                'new_items_by_location':
                    self.new_items_by_location(lib.pid),
                'loans_of_transaction_library_by_item_location':
                    self.loans_of_transaction_library_by_item_location(
                        libraries_map,
                        lib.pid,
                        [ItemCirculationAction.CHECKIN,
                         ItemCirculationAction.CHECKOUT])
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

    def checkouts_for_transaction_library(self, library_pid, trigger):
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

    def checkouts_for_owning_library(self, library_pid, trigger):
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

    def active_patrons_by_postal_code(self, library_pid, trigger):
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
            elif patron_pid not in patron_pids:
                stats[postal_code] += 1
            patron_pids.add(patron_pid)
        return stats

    def new_active_patrons_by_postal_code(self, library_pid, trigger):
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
                elif patron_pid not in patron_pids:
                    stats[postal_code] += 1
                patron_pids.add(patron_pid)

        return stats

    def new_documents(self, library_pid):
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

    def renewals(self, library_pid, trigger):
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

    def validated_requests(self, library_pid, trigger):
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

    def new_items_by_location(self, library_pid):
        """Number of new items per library by location.

        Note: items created and then deleted during the time interval
        are not included.
        :param library_pid: string - the library to filter with
        :return: the number of matched documents
        :rtype: dict
        """
        search = ItemsSearch()[:0]\
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

    def items_by_document_type_and_subtype(self, library_pid):
        """Number of items per library by document type and sub-type.

        Note: if item has more than one doc type/subtype the item is counted
        multiple times
        :param library_pid: string - the library to filter with
        :return: the number of matched documents
        :rtype: dict
        """
        search = ItemsSearch()[:0]\
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
        stats = {
            bucket.key: bucket.doc_count
            for bucket in res.aggregations.main_type.buckets
        }
        for bucket in res.aggregations.subtype.buckets:
            stats[bucket.key] = bucket.doc_count
        return stats

    def loans_of_transaction_library_by_item_location(self,
                                                      libraries_map,
                                                      library_pid,
                                                      trigger):
        """Number of circulation operation during the specified timeframe.

        Number of loans of items by location when transaction location
        is equal to any of the library locations
        :param libraries_map: dict - map of library pid and name
        :param library_pid: string - the library to filter with
        :param trigger: string - action name (checkin, checkout)
        :return: the number of matched circulation operation
        :rtype: dict
        """
        location_pids = self._get_locations_pid(library_pid)
        search = RecordsSearch(index=LoanOperationLog.index_name)\
            .filter('range', date=self.date_range)\
            .filter('terms', loan__trigger=trigger)\
            .filter('terms', loan__transaction_location__pid=location_pids)\
            .source('loan').scan()

        stats = {}
        for s in search:
            item_library_pid = s.loan.item.library_pid
            item_library_name = libraries_map[item_library_pid]
            location_name = s.loan.item.holding.location_name

            key = f'{item_library_pid}: {item_library_name} - {location_name}'
            stats.setdefault(key, {
                'location_name': location_name,
                ItemCirculationAction.CHECKIN: 0,
                ItemCirculationAction.CHECKOUT: 0})
            stats[key][s.loan.trigger] += 1
        return stats


class StatsReport:
    """Statistics for report."""

    def __init__(self):
        """Constructor.

        Set variables to create report.
        """
        self.indicators = [StatIndicators.NUMBER_OF_DOCUMENTS,
                           StatIndicators.NUMBER_OF_SERIAL_HOLDINGS,
                           StatIndicators.NUMBER_OF_ITEMS,
                           StatIndicators.NUMBER_OF_PATRONS,
                           StatIndicators.NUMBER_OF_ACTIVE_PATRONS,
                           StatIndicators.NUMBER_OF_ILL_REQUESTS,
                           StatIndicators.NUMBER_OF_DELETED_ITEMS,
                           StatIndicators.NUMBER_OF_CHECKINS,
                           StatIndicators.NUMBER_OF_CHECKOUTS,
                           StatIndicators.NUMBER_OF_RENEWALS,
                           StatIndicators.NUMBER_OF_REQUESTS]

        self.libraries = {library.pid: library
                          for library in Library.get_all()}

        self.organisations = Organisation.get_all()

        self.locations = {loc.pid: loc for loc in Location.get_all()}

        self.trigger_mapping = \
            {StatIndicators.NUMBER_OF_CHECKINS: ItemCirculationAction.CHECKIN,
             StatIndicators.NUMBER_OF_CHECKOUTS:
                ItemCirculationAction.CHECKOUT,
             StatIndicators.NUMBER_OF_RENEWALS: ItemCirculationAction.EXTEND,
             StatIndicators.NUMBER_OF_REQUESTS: ItemCirculationAction.REQUEST}

        self.distributions_mapping = {
                        StatIndicators.NUMBER_OF_DOCUMENTS: {
                            StatDistributions.LIBRARY:
                                'holdings.organisation.library_pid',
                            # StatDistributions.IMPORTED:
                            #   'adminMetadata.source', #TODO
                            StatDistributions.TIME_RANGE_MONTH:
                                {'_created': 'month'},
                            StatDistributions.TIME_RANGE_YEAR:
                                {'_created': 'year'}},
                        StatIndicators.NUMBER_OF_SERIAL_HOLDINGS: {
                            StatDistributions.LIBRARY: 'library.pid',
                            StatDistributions.TIME_RANGE_MONTH:
                                {'_created': 'month'},
                            StatDistributions.TIME_RANGE_YEAR:
                                {'_created': 'year'}},
                        StatIndicators.NUMBER_OF_ITEMS: {
                            StatDistributions.LIBRARY: 'library.pid',
                            StatDistributions.LOCATION: 'location.pid',
                            StatDistributions.TYPE: 'type',
                            StatDistributions.TIME_RANGE_MONTH:
                                {'_created': 'month'},
                            StatDistributions.TIME_RANGE_YEAR:
                                {'_created': 'year'}},
                        StatIndicators.NUMBER_OF_DELETED_ITEMS: {
                            StatDistributions.LIBRARY: 'library.value',
                            # StatDistributions.ITEM_LOCATION: '', #TODO
                            StatDistributions.TYPE: 'type',
                            StatDistributions.TIME_RANGE_MONTH:
                                {'_created': 'month'},
                            StatDistributions.TIME_RANGE_YEAR:
                                {'_created': 'year'}},
                        StatIndicators.NUMBER_OF_ILL_REQUESTS: {
                            StatDistributions.LIBRARY: 'library.pid',
                            StatDistributions.STATUS: 'status',
                            StatDistributions.TIME_RANGE_MONTH:
                                {'_created': 'month'},
                            StatDistributions.TIME_RANGE_YEAR:
                                {'_created': 'year'}},
                        'number_of_circ_operations': {
                            StatDistributions.LIBRARY:
                                'loan.item.library_pid',
                            # StatDistributions.ITEM_OWNING_LIBRARY: '' #TODO
                            # StatDistributions.ITEM_LOCATION: '' #TODO
                            StatDistributions.PATRON_TYPE: 'loan.patron.type',
                            StatDistributions.DOCUMENT_TYPE:
                                'loan.item.document.type',
                            StatDistributions.TRANSACTION_CHANNEL:
                                'loan.transaction_channel',
                            StatDistributions.LOCATION:
                                'loan.pickup_location.pid',
                            StatDistributions.TIME_RANGE_MONTH:
                                {'_created': 'month'},
                            StatDistributions.TIME_RANGE_YEAR:
                                {'_created': 'year'}},
                        StatIndicators.NUMBER_OF_PATRONS: {
                            StatDistributions.GENDER: 'gender',
                            StatDistributions.ROLE: 'roles',
                            StatDistributions.TIME_RANGE_MONTH:
                                {'_created': 'month'},
                            StatDistributions.TIME_RANGE_YEAR:
                                {'_created': 'year'},
                        },
                        # StatIndicators.NUMBER_OF_ACTIVE_PATRONS: {
                        # StatDistributions.LIBRARY: '',
                        # StatDistributions.GENDER: 'gender',
                        # StatDistributions.PATRON_POSTAL_CODE: 'postal_code',
                        # StatDistributions.TIME_RANGE_MONTH:
                        #   {'_created': 'month'},
                        # StatDistributions.TIME_RANGE_YEAR:
                        #   {'_created': 'year'},
                        # } #TODO
                        }

        self.query_mapping = {
            StatIndicators.NUMBER_OF_CHECKINS: {
                'class': RecordsSearch(index=LoanOperationLog.index_name)[:0],
                'filters':
                    [
                        Q('term', record__type='loan'),
                        Q('term', loan__trigger=ItemCirculationAction.CHECKIN)
                    ]
            },
            StatIndicators.NUMBER_OF_CHECKOUTS: {
                'class': RecordsSearch(index=LoanOperationLog.index_name)[:0],
                'filters':
                    [
                        Q('term', record__type='loan'),
                        Q('term', loan__trigger=ItemCirculationAction.CHECKOUT)
                    ]
            },
            StatIndicators.NUMBER_OF_RENEWALS: {
                'class': RecordsSearch(index=LoanOperationLog.index_name)[:0],
                'filters':
                    [
                        Q('term', record__type='loan'),
                        Q('term', loan__trigger=ItemCirculationAction.EXTEND)
                    ]
            },
            StatIndicators.NUMBER_OF_REQUESTS: {
                'class': RecordsSearch(index=LoanOperationLog.index_name)[:0],
                'filters':
                    [
                        Q('term', record__type='loan'),
                        Q('term', loan__trigger=ItemCirculationAction.REQUEST)
                    ]
            },
            StatIndicators.NUMBER_OF_DOCUMENTS: {
                'class': DocumentsSearch()[:0],
                'filters': []
            },
            StatIndicators.NUMBER_OF_ITEMS: {
                'class': ItemsSearch()[:0],
                'filters': []
            },
            StatIndicators.NUMBER_OF_SERIAL_HOLDINGS: {
                'class': HoldingsSearch()[:0],
                'filters': [Q('term', holdings_type='serial')]
            },
            StatIndicators.NUMBER_OF_ILL_REQUESTS: {
                'class': ILLRequestsSearch()[:0],
                'filters': []
            },
            StatIndicators.NUMBER_OF_DELETED_ITEMS: {
                'class': RecordsSearch(index=LoanOperationLog.index_name)[:0],
                'filters': [Q('term', record__type='item'),
                            Q('term', operation='delete')]
            },
            StatIndicators.NUMBER_OF_PATRONS: {
                'class': PatronsSearch()[:0],
                'filters': []
            }
        }

        self.config = {}

        self.size = 10000

    def _format_bucket_key(self, dist, bucket_dist):
        """Format name of distribution to add in the results file.

        :param dist: distribution name
        :param bucket_dist: bucket of the distribution
        :returns: formatted name of distribution
        """
        bucket_key_formatted = None
        if dist in [StatDistributions.LOCATION,
                    StatDistributions.ITEM_LOCATION]:
            if loc := self.locations.get(bucket_dist.key):
                bucket_key_formatted = f'{loc["code"]}: {loc["name"]}'

        if dist in [StatDistributions.TIME_RANGE_MONTH,
                    StatDistributions.TIME_RANGE_YEAR]:
            date = ciso8601.parse_datetime(bucket_dist.key_as_string)
            if dist == StatDistributions.TIME_RANGE_YEAR:
                bucket_key_formatted = date.strftime('%Y')
            else:
                bucket_key_formatted = date.strftime('%Y-%m')

        return bucket_key_formatted or bucket_dist.key

    def _query_results_by_library(self, res):
        """Process bucket results when one of the distributions is 'library'.

        :param res: results of the query
        :returns: formatted results
        """
        indicator = self.config['indicator']
        dist2 = self.config['dist2']
        library_pids = self.config['library_pids']

        results = []

        def bucket_one_distribution(results):
            """Process results for one distribution."""
            if bucket_dist1.doc_count:
                results.append({
                    'org_pid': library.get_organisation().get('pid'),
                    'library_pid': library.pid,
                    'library_name': library.get('name'),
                    indicator: bucket_dist1.doc_count
                })
            return results

        def bucket_two_distributions(results):
            """Process results for two distributions."""
            for bucket_dist2 in bucket_dist1.dist2.buckets:
                if bucket_dist2.doc_count:
                    key_dist2 =\
                        self._format_bucket_key(dist2,
                                                bucket_dist2)
                    results.append({
                        'org_pid': library.get_organisation().get('pid'),
                        'library_pid': library.pid,
                        'library_name': library.get('name'),
                        dist2: key_dist2,
                        indicator: bucket_dist2.doc_count
                    })
            return results

        for bucket in res.aggregations:
            for bucket_dist1 in bucket.buckets:
                if bucket_dist1.key in library_pids\
                 and (library := self.libraries.get(bucket_dist1.key)):
                    if dist2:
                        results = bucket_two_distributions(results)
                    else:
                        results = bucket_one_distribution(results)

        return results

    def _query_results_by_organisation(self, res):
        """Process bucket results when none of the distributions is 'library'.

        :param res: results of the query
        :returns: formatted results
        """
        indicator = self.config['indicator']
        dist1 = self.config['dist1']
        dist2 = self.config['dist2']

        results = []

        def bucket_one_distribution(results):
            """Process results for one distribution."""
            if bucket_dist1.doc_count:
                results.append({'org_pid': self.config['org_pid'],
                                dist1: key_dist1,
                                indicator: bucket_dist1.doc_count})
            return results

        def bucket_two_distributions(results):
            """Process results for two distributions."""
            for bucket_dist2 in bucket_dist1.dist2.buckets:
                key_dist2 = self._format_bucket_key(dist2,
                                                    bucket_dist2)
                if bucket_dist2.doc_count:
                    results.append({'org_pid': self.config['org_pid'],
                                    dist1: key_dist1,
                                    dist2: key_dist2,
                                    indicator: bucket_dist2.doc_count})
            return results

        for bucket in res.aggregations:
            for bucket_dist1 in bucket:
                key_dist1 = self._format_bucket_key(dist1, bucket_dist1)
                if dist2:
                    results = bucket_two_distributions(results)
                else:
                    results = bucket_one_distribution(results)

        return results

    def _swap_distributions(self, dist1, dist2):
        """Re-arrange dist1 and dist2.

        :param dist1: distribution1
        :param dist2: distribution2
        """
        if dist1 in [StatDistributions.TIME_RANGE_MONTH,
                     StatDistributions.TIME_RANGE_YEAR] and dist2:
            self.config['dist1'] = dist2
            self.config['dist2'] = dist1
        elif dist2 == 'library':
            self.config['dist1'] = dist2
            self.config['dist2'] = dist1

    def _query_aggs(self, query, fields):
        """Create aggregations and execute query.

        :param query: query
        :param fields: index fields on which to make the aggregations
        :returns: results of query
        """
        indicator = self.config['indicator']
        dist1 = self.config['dist1']
        dist2 = self.config['dist2']
        filter = self.config['filter']
        period = self.config['period']
        library_pids = self.config['library_pids']
        org_pid = self.config['org_pid']

        self._swap_distributions(dist1, dist2)
        dist1 = self.config['dist1']
        dist2 = self.config['dist2']

        if dist1:
            field1 = fields[dist1]
        if dist2:
            field2 = fields[dist2]

        # CASE: no distributions
        if not dist1 and not dist2:
            return [{'org_pid': org_pid, indicator: query.count()}]

        if dist2:
            if dist2 in [StatDistributions.TIME_RANGE_MONTH,
                         StatDistributions.TIME_RANGE_YEAR]:
                field_time_range = list(fields[dist2].keys())[0]
                value_time_range = fields[dist2][field_time_range]
                query.aggs\
                    .bucket('dist1', 'terms', field=field1, size=self.size)\
                    .bucket('dist2', 'date_histogram',
                            field=field_time_range,
                            calendar_interval=value_time_range)
            else:
                query.aggs\
                    .bucket('dist1', 'terms', field=field1, size=self.size)\
                    .bucket('dist2', 'terms', field=field2, size=self.size)
        else:
            if dist1 in [StatDistributions.TIME_RANGE_MONTH,
                         StatDistributions.TIME_RANGE_YEAR]:
                field_time_range = list(fields[dist1].keys())[0]
                value_time_range = fields[dist1][field_time_range]
                query.aggs\
                    .bucket('dist1', 'date_histogram',
                            field=field_time_range,
                            calendar_interval=value_time_range)
            else:
                query.aggs\
                    .bucket('dist1', 'terms', field=field1, size=self.size)

        res = query.execute()

        # CASE: aggregation by library
        if dist1 == StatDistributions.LIBRARY:
            return self._query_results_by_library(res)

        # CASE: aggregation by organisation
        return self._query_results_by_organisation(res)

    def _number_of(self, query):
        """Add filter and aggregations to query.

        :param query: main index query
        :returns: results of the query
        """
        indicator = self.config['indicator']
        filter = self.config['filter']
        period = self.config['period']
        library_pids = self.config['library_pids']

        if self.trigger_mapping.get(indicator):
            fields = self.distributions_mapping['number_of_circ_operations']
        else:
            fields = self.distributions_mapping[indicator]

        # filter by organisation
        if indicator == StatIndicators.NUMBER_OF_PATRONS:
            org_filter = Q('term', organisation__pid=self.config['org_pid'])
            query = query.filter('bool', must=[org_filter])
        else:
            # filter by organisation libraries
            org_filter = Q('terms', **{fields['library']: library_pids})
            query = query.filter('bool', must=[org_filter])

        # add filter to query
        if filter:
            cfg_filter = Q('query_string', query=(filter))
            query = query.filter('bool', must=[cfg_filter])

        # add filter period to query
        if period:
            if period == 'month':
                # previous month
                previous_month = datetime.now() - relativedelta(months=1)
                # get last day of previous month using relativedelta with
                # day=31
                previous_month = previous_month + relativedelta(day=31)
                month = '%02d' % previous_month.month
                _from = f'{previous_month.year}-{month}-01T00:00:00'
                _to = f'{previous_month.year}-{month}-{previous_month.day}'
                _to = f'{_to}T23:59:59'
            else:
                previous_year = datetime.now().year - 1
                _from = f'{previous_year}-01-01T00:00:00'
                _to = f'{previous_year}-12-31T23:59:59'

            query = query\
                .filter('range', _created={'gte': _from, 'lte': _to})

        # make aggregations according to distributions and execute query
        return self._query_aggs(query, fields)

    def _validate_distributions(self, distributions):
        """Validate distributions of statistics report.

        :param distributions: distributions of the configuration.
        :raises StatReportDistributionsValidatorException
        if configuration contains errors
        """
        # check unicity into distributions keys
        if (len(set(distributions)) != len(distributions)):
            raise StatReportDistributionsValidatorException(
                'Distributions should not be the same.')
        # check time_range_month and time_range_year are not both
        # selected
        if StatDistributions.TIME_RANGE_MONTH in distributions and \
           StatDistributions.TIME_RANGE_YEAR in distributions:
            raise StatReportDistributionsValidatorException(
                'Distributions should not be both time_range_month and '
                'time_range_year')
        # check different type of location searches are not selected
        if StatDistributions.ITEM_LOCATION in distributions and \
           StatDistributions.LOCATION in distributions:
            raise StatReportDistributionsValidatorException(
                'Distributions should not be both item_location and '
                'location')
        # check different type of library searches are not selected
        if StatDistributions.LIBRARY in distributions and \
           StatDistributions.ITEM_OWNING_LIBRARY in distributions:
            raise StatReportDistributionsValidatorException(
                'Distributions should not be both library and '
                'item_owning_library')

    def _report_data(self, data):
        """Collect data for report.

        :param data: report configuration data
        :returns: results data of report
        """
        org_pid = extracted_data_from_ref(data['organisation'])
        org = Organisation.get_record_by_pid(org_pid)
        library_pids = list(org.get_libraries_pids())

        indicator = data['category'].get('indicator')
        distributions = indicator.get('distributions')

        if distributions:
            if len(distributions) == 1:
                dist1 = distributions[0]
                dist2 = None
            elif len(distributions) == 2:
                try:
                    self._validate_distributions(distributions)
                except StatReportDistributionsValidatorException as e:
                    raise ValidationError(str(e)) from e
                dist1 = distributions[0]
                dist2 = distributions[1]
            else:
                return
        else:
            dist1 = None
            dist2 = None

        self.config = {'indicator': indicator.get('type'),
                       'dist1': dist1,
                       'dist2': dist2,
                       'filter': indicator.get('filter'),
                       'period': indicator.get('period'),
                       'frequency': data['frequency'],
                       'library_pids': library_pids,
                       'org_pid': org_pid}

        indicator = self.config["indicator"]

        query = self.query_mapping[indicator].get('class')
        query_filter = Q()
        for q_filter in self.query_mapping[indicator].get('filters'):
            query_filter &= q_filter
        query = query.filter('bool', must=[query_filter])

        return self._number_of(query) if query else []

    def create(self, pid, dbcommit=False, reindex=False):
        """Create report.

        :param pid: report configuration pid
        """
        cfg = StatConfiguration.get_record_by_pid(pid)
        if not cfg.get('is_active'):
            raise NotActiveStatConfigException(pid)

        results = self._report_data(cfg)

        # case query results is empty
        if not results:
            results = [{'org_pid': self.config['org_pid'],
                        self.config['indicator']: 0}]

        data = dict(
            type='report',
            config=cfg,
            values=results
        )
        return Stat.create(data, dbcommit=dbcommit, reindex=reindex)


class StatsIndexer(IlsRecordsIndexer):
    """Indexing stats in Elasticsearch."""

    record_cls = Stat

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(record_id_iterator, doc_type='stat')
