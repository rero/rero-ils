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

"""To compute the statistics for librarian."""


import hashlib
from datetime import datetime

import arrow
from dateutil.relativedelta import relativedelta
from invenio_search.api import RecordsSearch

from rero_ils.modules.items.api import ItemsSearch
from rero_ils.modules.items.models import ItemCirculationAction
from rero_ils.modules.libraries.api import LibrariesSearch
from rero_ils.modules.loans.logs.api import LoanOperationLogsSearch
from rero_ils.modules.locations.api import LocationsSearch
from rero_ils.modules.operation_logs.api import OperationLog
from rero_ils.modules.patrons.api import PatronsSearch

from .pricing import StatsForPricing


class StatsForLibrarian(StatsForPricing):
    """Statistics for librarian.

    TODO: the type of the statistic should be changed from
          librarian to library.
    """

    def __init__(self, to_date=None):
        """Constructor.

        :param to_date: end date of the statistics date range
        """
        if to_date and isinstance(to_date, datetime):
            to_date = arrow.Arrow.fromdatetime(to_date)
        to_date = to_date or arrow.utcnow() - relativedelta(days=1)
        # Get statistics per month
        _from = f'{to_date.year}-{to_date.month:02d}-01T00:00:00'
        _to = to_date.format(fmt='YYYY-MM-DDT23:59:59')
        self.date_range = {'gte': _from, 'lte': _to}

    def _get_locations_code_name(self, location_pids):
        """Location code and name.

        :param location_pid: string - the location to filter with
        :return: concatenated code and name of location
        :rtype: string
        """
        location_search = LocationsSearch()\
            .filter('terms', pid=location_pids)\
            .source(['code', 'name', 'pid'])
        res = {}
        for hit in location_search.scan():
            res[hit.pid] = f'{hit.code} - {hit.name}'
        return res

    def process(self, library):
        """Process statistics for a give library.

        :param library: library from the elasticsearch index
        :return: a dict containing all the processed values.
        """
        return {
            'checkouts_for_transaction_library':
                self.checkouts_for_transaction_library(library.pid),
            'checkouts_for_owning_library':
                self.checkouts_for_owning_library(library.pid),
            'active_patrons_by_postal_code':
                self.active_patrons_by_postal_code(library.pid),
            'new_active_patrons_by_postal_code':
                self.active_patrons_by_postal_code(
                    library.pid, new_patrons=True),
            'new_documents':
                self.new_documents(library.pid),
            'new_items':
                self.number_of_new_items(library.pid),
            'renewals':
                self.renewals(library.pid),
            'validated_requests':
                self.validated_requests(library.pid),
            'items_by_document_type_and_subtype':
                self.items_by_document_type_and_subtype(library.pid),
            'new_items_by_location':
                self.new_items_by_location(library.pid),
            'loans_of_transaction_library_by_item_location':
                self.loans_of_transaction_library_by_item_location(library.pid)
        }

    def checkouts_for_transaction_library(self, library_pid):
        """Number of circulation operation during the specified timeframe.

        Number of loans of items when transaction location is equal to
        any of the library locations
        :param library_pid: string - the library to filter with
        :return: the number of matched circulation operation
        :rtype: integer
        """
        location_pids = LocationsSearch().location_pids(library_pid)
        return LoanOperationLogsSearch().get_logs_by_trigger(
                triggers=[ItemCirculationAction.CHECKOUT],
                date_range=self.date_range
            ).filter('terms', loan__transaction_location__pid=location_pids)\
            .count()

    def checkouts_for_owning_library(self, library_pid):
        """Number of circulation operation during the specified timeframe.

        Number of loans of items per library when the item is owned by
        the library
        :param library_pid: string - the library to filter with
        :return: the number of matched circulation operation
        :rtype: integer
        """
        return LoanOperationLogsSearch().get_logs_by_trigger(
                triggers=[ItemCirculationAction.CHECKOUT],
                date_range=self.date_range
            ).filter('term', loan__item__library_pid=library_pid)\
            .count()

    def active_patrons_by_postal_code(self, library_pid, new_patrons=False):
        """Number of circulation operation during the specified timeframe.

        Number of patrons per library and CAP when transaction location
        is equal to any of the library locations
        :param library_pid: string - the library to filter with
        :param new_patrons: bool - filter by new patrons
        :return: the number of matched circulation operation
        :rtype: dict
        """
        location_pids = LocationsSearch().location_pids(library_pid)

        search = LoanOperationLogsSearch().get_logs_by_trigger(
                triggers=[
                    ItemCirculationAction.REQUEST,
                    ItemCirculationAction.CHECKIN,
                    ItemCirculationAction.CHECKOUT
                ], date_range=self.date_range
            ).filter('terms', loan__transaction_location__pid=location_pids)
        if new_patrons:
            # Get new patrons in date range and hash the pids
            search_patron = PatronsSearch()\
                .filter("range", _created=self.date_range)\
                .source('pid').scan()
            new_patron_hashed_pids = set()
            for p in search_patron:
                hashed_pid = hashlib.md5(p.pid.encode()).hexdigest()
                new_patron_hashed_pids.add(hashed_pid)
            search = search.filter(
                'terms', loan__patron__hashed_pid=list(new_patron_hashed_pids))
        stats = {}
        patron_pids = set()
        # Main postal code from user profile
        for s in search.scan():
            patron_pid = s.loan.patron.hashed_pid
            postal_code = 'unknown'
            if 'postal_code' in s.loan.patron:
                postal_code = s.loan.patron.postal_code

            stats.setdefault(postal_code, 0)
            if patron_pid not in patron_pids:
                stats[postal_code] += 1
                patron_pids.add(patron_pid)
        return stats

    def new_documents(self, library_pid):
        """Number of new documents per library for given time interval.

        :param library_pid: string - the library to filter with
        :return: the number of matched documents
        :rtype: integer
        """
        return RecordsSearch(index=OperationLog.index_name)\
            .filter('range', date=self.date_range)\
            .filter('term', record__type='doc')\
            .filter('term', operation='create')\
            .filter('term', library__value=library_pid)\
            .count()

    def renewals(self, library_pid):
        """Number of items with loan extended.

        Number of items with loan extended per library for given time interval
        :param library_pid: string - the library to filter with
        :return: the number of matched documents
        :rtype: integer
        """
        return LoanOperationLogsSearch().get_logs_by_trigger(
                triggers=[ItemCirculationAction.EXTEND],
                date_range=self.date_range
            ).filter('term', loan__item__library_pid=library_pid).count()

    def validated_requests(self, library_pid):
        """Number of validated requests.

        Number of validated requests per library for given time interval
        Match is done on the library of the librarian.
        :param library_pid: string - the library to filter with
        :return: the number of matched documents
        :rtype: integer
        """
        return LoanOperationLogsSearch().get_logs_by_trigger(
                triggers=['validate_request'],
                date_range=self.date_range
            ).filter('term', library__value=library_pid).count()

    def new_items_by_location(self, library_pid):
        """Number of new items per library by location.

        Note: items created and then deleted during the time interval
        are not included.
        :param library_pid: string - the library to filter with
        :return: the number of matched documents
        :rtype: dict
        """
        location_pids = LocationsSearch().location_pids(library_pid)

        search = ItemsSearch()[:0]\
            .filter('range', _created=self.date_range)\
            .filter('term', library__pid=library_pid)\
            .source('location.pid')
        search.aggs.bucket('location_pid', 'terms', field='location.pid',
                           size=10000)
        res = search.execute()
        stats = {}
        location_pids = [
            bucket.key for bucket in res.aggregations.location_pid.buckets]
        location_names = self._get_locations_code_name(location_pids)
        for bucket in res.aggregations.location_pid.buckets:
            stats[location_names[bucket.key]] = bucket.doc_count
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

    def loans_of_transaction_library_by_item_location(self, library_pid):
        """Number of circulation operation during the specified timeframe.

        Number of loans of items by location when transaction location
        is equal to any of the library locations
        :param library_pid: string - the library to filter with
        :return: the number of matched circulation operation
        :rtype: dict
        """
        location_pids = LocationsSearch().location_pids(library_pid)

        search = LoanOperationLogsSearch().get_logs_by_trigger(
                triggers=[
                    ItemCirculationAction.CHECKIN,
                    ItemCirculationAction.CHECKOUT
                ], date_range=self.date_range
            ).filter('terms', loan__transaction_location__pid=location_pids)\
            .source('loan').scan()

        stats = {}
        libraries_map = {lib.pid: lib.name for lib in LibrariesSearch().source(
            ['pid', 'name', 'organisation']).scan()}
        for s in search:
            item_library_pid = s.loan.item.library_pid
            item_library_name = libraries_map[item_library_pid]
            location_name = s.loan.item.holding.location_name

            key = f'{item_library_pid}: {item_library_name} - {location_name}'
            stats.setdefault(key, {
                # TODO: to be removed as it is already in the key
                'location_name': location_name,
                ItemCirculationAction.CHECKIN: 0,
                ItemCirculationAction.CHECKOUT: 0})
            stats[key][s.loan.trigger] += 1
        return stats
