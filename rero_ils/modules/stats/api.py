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
from datetime import datetime
from functools import partial

import arrow
from dateutil.relativedelta import relativedelta
from elasticsearch_dsl.query import Q
from flask import current_app
from invenio_search.api import DefaultFilter, RecordsSearch

from rero_ils.modules.acq_order_lines.api import AcqOrderLinesSearch
from rero_ils.modules.api import IlsRecord, IlsRecordsIndexer, IlsRecordsSearch
from rero_ils.modules.documents.api import DocumentsSearch
from rero_ils.modules.fetchers import id_fetcher
from rero_ils.modules.holdings.api import HoldingsSearch
from rero_ils.modules.ill_requests.api import ILLRequestsSearch
from rero_ils.modules.ill_requests.models import ILLRequestStatus
from rero_ils.modules.items.api import ItemsSearch
from rero_ils.modules.items.models import ItemCirculationAction
from rero_ils.modules.libraries.api import LibrariesSearch
from rero_ils.modules.loans.logs.api import LoanOperationLog
from rero_ils.modules.locations.api import Location, LocationsSearch
from rero_ils.modules.minters import id_minter
from rero_ils.modules.organisations.api import Organisation
from rero_ils.modules.patrons.api import Patron, PatronsSearch, \
    current_librarian
from rero_ils.modules.providers import Provider
from rero_ils.modules.stats.models import StatIdentifier, StatMetadata
from rero_ils.modules.stats.permissions import permission_filter
from rero_ils.modules.stats_cfg.api import Stat_cfg
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

        default_filter = DefaultFilter(permission_filter)


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
            .filter(
                'terms',
                roles=[Patron.ROLE_LIBRARIAN, Patron.ROLE_SYSTEM_LIBRARIAN]
            )\
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
    """Statistics for librarian."""

    def __init__(self, to_date=None):
        """Constructor.

        :param to_date: end date of the statistics date range
        """
        self.to_date = to_date or arrow.utcnow() - relativedelta(days=1)
        # Get statistics per month
        _from = f'{self.to_date.year}-{self.to_date.month:02d}-01T00:00:00'
        _to = self.to_date.format(fmt='YYYY-MM-DDT23:59:59')
        self.date_range = {'gte': _from, 'lte': _to}

    @classmethod
    def get_librarian_library_pids(cls):
        """Get libraries pids of librarian.

        Note: for system_librarian includes libraries of organisation.
        """
        if Patron.ROLE_LIBRARIAN in current_librarian["roles"]:
            library_pids = {
                extracted_data_from_ref(lib) for lib in
                current_librarian.get('libraries', [])}

        # case system_librarian: add libraries of organisation
        if Patron.ROLE_SYSTEM_LIBRARIAN in current_librarian["roles"]:
            patron_organisation = current_librarian.get_organisation()
            libraries_search = LibrariesSearch()\
                .filter('term', organisation__pid=patron_organisation.pid)\
                .source(['pid']).scan()
            library_pids = library_pids.union(
                {s.pid for s in libraries_search})
        return list(library_pids)

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

    def items_by_document_type_and_subtype(self, library_pid):
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
        self.indicators = ['number_of_checkouts', 'number_of_checkins',
                           'number_of_renewals', 'number_of_requests',
                           'number_of_documents',
                           'number_of_created_documents',
                           'number_of_items', 'number_of_created_items',
                           'number_of_deleted_items',
                           'number_of_holdings', 'number_of_created_holdings',
                           'number_of_patrons', 'number_of_active_patrons',
                           'number_of_ill_requests']

        self.libraries = [{'pid': lib.pid, 'name': lib.name,
                           'org_pid': lib.organisation.pid}
                          for lib in StatsForLibrarian().get_all_libraries()]

        self.organisations = Organisation.get_all()
        self.locations = self.get_all_locations()

        self.trigger_mapping = \
            {'number_of_checkouts': ItemCirculationAction.CHECKOUT,
             'number_of_checkins': ItemCirculationAction.CHECKIN,
             'number_of_renewals': ItemCirculationAction.EXTEND,
             'number_of_requests': ItemCirculationAction.REQUEST}

        self.distributions_mapping = {
                        'number_of_documents': {
                             'library': 'holdings.organisation.library_pid',
                             'time_range': {'_created': 'month'}},
                        'number_of_items': {
                             'library': 'library.pid',
                             'location': 'location.pid',
                             'type': 'type',
                             'time_range': {'_created': 'month'}},
                        'number_of_circ_operations': {
                             'library': 'loan.item.library_pid',
                             'patron_type': 'loan.patron.type',
                             'document_type': 'loan.item.document.type',
                             'transaction_channel': 'loan.transaction_channel',
                             'pickup_location': 'loan.pickup_location.pid',
                             'time_range': {'date': 'month'}},
                        'number_of_holdings': {
                             'library': 'library.pid',
                             'holding_type': 'holdings_type',
                             'time_range': {'_created': 'month'}},
                        'number_of_ill_requests': {
                                         'library': 'library.pid',
                                         'status': 'status',
                                         'loan_status': 'loan_status',
                                         'time_range': {'_created': 'month'}},
                        'number_of_patrons': {
                                          'library': 'patron.libraries.pid',
                                          'local_code': 'local_codes',
                                          'role': 'roles',
                                          'time_range': {'_created': 'month'}},
                        'number_of_created_documents': {
                                            'library': 'library.value',
                                            'time_range': {'date': 'month'}},
                        'number_of_deleted_items': {
                                             'library': 'library.value',
                                             'time_range': {'date': 'month'}},
                        'number_of_created_items': {
                                             'library': 'library.value',
                                             'time_range': {'date': 'month'}},
                        'number_of_created_holdings': {
                                             'library': 'library.value',
                                             'time_range': {'date': 'month'}},
                        'number_of_active_patrons': {}
                        }

        self.filter_indexes = {'operation_logs':
                               {'items': 'loan.item.pid',
                                'holdings': 'loan.holding.pid',
                                'patrons': 'loan.patron.pid',
                                'documents': 'loan.item.document.pid'}
                               }

        # the default value is 65536
        # the maximum value that can be set is 2147483647
        self.limit_pids = 65536

        self.config = {}

    def get_library_pids(self, org_pid):
        """Get libraries pids of organisation."""
        libraries_search = LibrariesSearch()\
            .filter('term', organisation__pid=org_pid)\
            .source(['pid']).scan()
        return [s.pid for s in libraries_search]

    def get_all_locations(self):
        """Get all locations.

        :returns: formatted location names
        """
        locations = []
        for pid in Location.get_all_pids():
            record = Location.get_record_by_pid(pid)
            locations.append({pid: f'{record["code"]}: {record["name"]}'})
        return locations

    def format_bucket_key(self, dist, bucket_dist):
        """Format name of distribution to add in the results file.

        :param dist: distribution name
        :param bucket_dist: bucket of the distribution
        :returns: formatted name of distribution
        """
        bucket_key_formatted = None
        if dist in ['location', 'pickup_location']:
            bucket_key_formatted = [v for loc in self.locations
                                    for k, v in loc.items()
                                    if k == bucket_dist.key]
            if bucket_key_formatted:
                bucket_key_formatted = bucket_key_formatted[0]

        if dist == 'time_range':
            date, _ = bucket_dist.key_as_string.split('T')
            date = datetime.strptime(date, '%Y-%m-%d')
            if self.config['period'] == 'year':
                bucket_key_formatted = f'{date.year}'
            else:
                bucket_key_formatted = f'{date.year}-{date.month}'

        return bucket_key_formatted or bucket_dist.key

    def query_results_1(self, res):
        """Process bucket results.

        Library is in distribution 1
        :param res: result of query
        :returns: formatted results
        """
        indicator = self.config['indicator']
        dist2 = self.config['dist2']
        library_pids = self.config['library_pids']

        results = []
        for bucket in res.aggregations:
            for bucket_dist0 in bucket.buckets:
                library = [lib for lib in self.libraries
                           if lib['pid'] == bucket_dist0.key and
                           lib['pid'] in library_pids]
                if library:
                    for bucket_dist2 in bucket_dist0.dist2.buckets:
                        key_dist2 = self.format_bucket_key(dist2, bucket_dist2)
                        if bucket_dist2.doc_count:
                            results.append({dist2: key_dist2,
                                            'org_pid': library[0]['org_pid'],
                                            'library_pid': library[0]['pid'],
                                            'library_name': library[0]['name'],
                                            indicator: bucket_dist2.doc_count})
        return results

    def query_results_2(self, res):
        """Process bucket results.

        Library is not in distribution 1 or 2
        :param res: result of query
        :returns: formatted results
        """
        indicator = self.config['indicator']
        dist1 = self.config['dist1']
        dist2 = self.config['dist2']
        library_pids = self.config['library_pids']

        results = []
        for bucket in res.aggregations:
            for bucket_dist0 in bucket:
                library = [lib for lib in self.libraries
                           if lib['pid'] == bucket_dist0.key and
                           lib['pid'] in library_pids]
                for bucket_dist1 in bucket_dist0.dist1.buckets:
                    key_dist1 = self.format_bucket_key(dist1, bucket_dist1)
                    for bucket_dist2 in bucket_dist1.dist2.buckets:
                        key_dist2 = self.format_bucket_key(dist2, bucket_dist2)
                        if bucket_dist2.doc_count:
                            results.append({dist1: key_dist1,
                                            dist2: key_dist2,
                                            'org_pid': library[0]['org_pid'],
                                            'library_pid': library[0]['pid'],
                                            'library_name': library[0]['name'],
                                            indicator: bucket_dist2.doc_count})
        return results

    def query_filter_index(self, filter_index):
        """Query filter by index.

        :param filter_index: index of the filter
        :return: query for index
        """
        query_index = None
        library_pids = self.config['library_pids']

        if filter_index == 'items':
            query_index = ItemsSearch()[0:0]\
                            .filter('terms', library__pid=library_pids)
        elif filter_index == 'documents':
            query_index = \
                DocumentsSearch()[0:0]\
                .filter(
                    'terms',
                    holdings__organisation__library_pid=library_pids
                )
        elif filter_index == 'holdings':
            query_index = HoldingsSearch()[0:0]\
                            .filter('terms', library__pid=library_pids)
        elif filter_index == 'patrons':
            query_index = PatronsSearch()[0:0]\
                            .filter('terms',
                                    patron__libraries__pid=library_pids)
        return query_index

    def query_filter(self, query, main_index):
        """Add queries for filters to main query.

        :param query: query on the main index
        :param main_index: the index of the indicator

        :return: updated library pids and query
        """
        filters = self.config['filters']

        filter_pids = None

        if main_index in self.filter_indexes:
            filter_indexes = self.filter_indexes[main_index]

            for f in filters.items():
                filter_index = list(f)[0]
                if filter_index in filter_indexes and \
                   filter_index is not main_index:
                    query_index = self.query_filter_index(filter_index)
                    filter = filters[filter_index]
                    results_filter = query_index\
                        .filter('bool', must=[Q('query_string',
                                                query=(filter))])\
                        .source(['pid']).scan()
                    filter_pids = list(set([s.pid for s in results_filter]))

                    # check the number of pids found is less than the limit
                    if len(filter_pids) > self.limit_pids:
                        return

                    query =\
                        query\
                        .filter('bool',
                                must=[
                                    Q('terms',
                                      **{
                                       filter_indexes[filter_index]:filter_pids
                                      })
                                ])

        if main_index in filters:
            query = query\
                    .filter('bool', must=[
                        Q('query_string', query=(filters[main_index]))])

        return query

    def query_aggs(self, query, fields):
        """Create aggregations and execute query.

        :param query: indicator query
        :param fields: index fields on which to make the aggregations
        :returns: results of query
        """
        indicator = self.config['indicator']
        dist1 = self.config['dist1']
        dist2 = self.config['dist2']
        library_pids = self.config['library_pids']

        size = 10000
        field0 = fields['library']  # main filter
        field1 = fields[dist1]
        field2 = fields[dist2]

        if dist1 == 'library':
            if dist2 == 'time_range':
                field_time_range = list(fields['time_range'])
                value_time_range = fields['time_range'][field_time_range[0]]
                query.aggs\
                    .bucket('dist0', 'terms', field=field0, size=size)\
                    .bucket('dist2', 'date_histogram',
                            field=field_time_range[0],
                            calendar_interval=value_time_range)
            else:
                query.aggs\
                    .bucket('dist0', 'terms', field=field0, size=size)\
                    .bucket('dist2', 'terms', field=field2, size=size)

            res = query.execute()
            results = self.query_results_1(res)

        else:
            if dist2 == 'time_range':
                field_time_range = list(fields['time_range'])
                value_time_range = fields['time_range'][field_time_range[0]]
                query.aggs\
                    .bucket('dist0', 'terms', field=field0, size=size)\
                    .bucket('dist1', 'terms', field=field1, size=size)\
                    .bucket('dist2', 'date_histogram',
                            field=field_time_range[0],
                            calendar_interval=value_time_range)
            else:
                query.aggs\
                    .bucket('dist0', 'terms', field=field0, size=size)\
                    .bucket('dist1', 'terms', field=field1, size=size)\
                    .bucket('dist2', 'terms', field=field2, size=size)
            res = query.execute()
            results = self.query_results_2(res)

        return results

    def number_of(self, query, main_index, trigger=None):
        """Add filters and aggregations to query.

        :param query: main index query
        :param main_index: main index
        :param trigger: trigger checkin, checkout, extend or request
        """
        indicator = self.config['indicator']
        dist1 = self.config['dist1']
        dist2 = self.config['dist2']
        filters = self.config['filters']
        library_pids = self.config['library_pids']

        if trigger:
            fields = self.distributions_mapping['number_of_circ_operations']
        else:
            fields = self.distributions_mapping[indicator]

        query = query\
            .filter('bool', must=[
                    Q('terms', **{fields['library']:library_pids})])

        # add filter query
        if filters:
            query = self.query_filter(query, main_index)
            if not query:
                return "Exceeded the limit for number of pids: \
                        the report was not created."

        # swap distributions, always put time_range in dist2
        if 'time_range' == dist1:
            self.config['dist1'] = dist2
            self.config['dist2'] = 'time_range'

        # make aggregations according to distributions and execute query
        results = self.query_aggs(query, fields)

        return results

    def collect(self, data):
        """Collect data for report.

        :param data: report configuration data
        :returns: results for report
        """
        org_pid = data['org_pid']

        trigger = None
        results = []
        org = Organisation.get_record_by_pid(org_pid)
        library_pids = [pid for pid in org.get_libraries_pids()]

        self.config = {'indicator': data['indicator'],
                       'dist1': data['dist1'],
                       'dist2': data['dist2'],
                       'filters': data['filters'],
                       'library_pids': library_pids,
                       'librarian_pid': data['librarian_pid'],
                       'period': data['period']}

        indicator = self.config["indicator"]

        if indicator in list(self.trigger_mapping):
            trigger = self.trigger_mapping[indicator]

        # change time_range interval to year
        if self.config["period"] == 'year':
            if indicator in list(self.trigger_mapping):
                indicator_key = 'number_of_circ_operations'
            else:
                indicator_key = indicator
            time_range =\
                self.distributions_mapping[indicator_key]['time_range']
            time_range[next(iter(time_range.keys()))] = self.config["period"]
            self.distributions_mapping[indicator_key]['time_range'] =\
                time_range

        if indicator in list(self.trigger_mapping):
            query = RecordsSearch(index=LoanOperationLog.index_name)[0:0]\
                    .filter('term', record__type='loan')\
                    .filter('term', loan__trigger=trigger)
            results = self.number_of(query, 'operation_logs', trigger)
        elif indicator == 'number_of_created_documents':
            query = RecordsSearch(index=LoanOperationLog.index_name)[0:0]\
                    .filter('term', record__type='doc')\
                    .filter('term', operation='create')
            results = self.number_of(query, 'operation_logs')
        elif indicator == 'number_of_documents':
            query = DocumentsSearch()[0:0]
            results = self.number_of(query, 'documents')
        elif indicator == 'number_of_items':
            query = ItemsSearch()[0:0]
            results = self.number_of(query, 'items')
        elif indicator == 'number_of_holdings':
            query = HoldingsSearch()[0:0]
            results = self.number_of(query, 'holdings')
        elif indicator == 'number_of_ill_requests':
            query = ILLRequestsSearch()[0:0]
            results = self.number_of(query, 'ill_requests')
        elif indicator == 'number_of_deleted_items':
            query = RecordsSearch(index=LoanOperationLog.index_name)[0:0]\
                    .filter('term', record__type='item')\
                    .filter('term', operation='delete')
            results = self.number_of(query, 'operation_logs')
        elif indicator == 'number_of_created_items':
            query = RecordsSearch(index=LoanOperationLog.index_name)[0:0]\
                    .filter('term', record__type='item')\
                    .filter('term', operation='create')
            results = self.number_of(query, 'operation_logs')
        elif indicator == 'number_of_created_holdings':
            query = RecordsSearch(index=LoanOperationLog.index_name)[0:0]\
                    .filter('term', record__type='hold')\
                    .filter('term', operation='create')
            results = self.number_of(query, 'operation_logs')
        elif indicator == 'number_of_patrons':
            query = PatronsSearch()[0:0]
            results = self.number_of(query, 'patrons')
        elif indicator == 'number_of_active_patrons':
            pass

        # create the report even if there are no results
        if not results:
            results = [{self.config['dist1']: None,
                        self.config['dist2']: None,
                        self.config['indicator']: None,
                        'org_pid': org_pid}]

        return results

    def create(self, pid, dbcommit=False, reindex=False):
        """Create report.

        :param pid: report configuration pid
        """
        cfg = Stat_cfg.get_record_by_pid(pid)
        results = self.collect(cfg)
        if isinstance(results, list):
            return Stat.create(dict(type='report', config_pid=pid,
                                    values=results),
                               dbcommit=dbcommit, reindex=reindex)
        current_app.logger.warning(results)


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
