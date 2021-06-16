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
import arrow
from dateutil.relativedelta import relativedelta
from invenio_search.api import RecordsSearch

from ..acq_order_lines.api import AcqOrderLinesSearch
from ..documents.api import DocumentsSearch
from ..items.api import ItemsSearch
from ..libraries.api import LibrariesSearch
from ..loans.logs.api import LoanOperationLog
from ..patrons.api import PatronsSearch


class StatsForPricing:
    """Statistics for pricing."""

    def __init__(self):
        """Constructor."""
        self.now = arrow.utcnow()
        self.months_delta = 3
        _to = self.now.format(fmt='YYYY-MM-DDT23:59:59')
        _from = (self.now - relativedelta(
            months=self.months_delta)).format(fmt='YYYY-MM-DDT00:00:00')
        self.date_range = {'gte': _from, 'lte': _to}

    def get_all_libraries(self):
        """Get all libraries in the system."""
        return LibrariesSearch().source(['pid', 'name', 'organisation']).scan()

    def stats(self):
        """Compute all the statistics."""
        for lib in self.get_all_libraries():
            print(f'==== {lib.name} (pid: {lib.pid}) =====')
            print('# docs', self.number_of_documents(lib.pid))
            print('# libs', self.number_of_libraries(lib.organisation.pid))
            print('# profs', self.number_of_librarians(lib.pid))
            print('# active patrons', self.number_of_active_patrons(lib.pid))
            print('# order lines', self.number_of_order_lines(lib.pid))
            print('# checkouts',
                  self.number_of_circ_operations(lib.pid, 'checkout'))
            print('# renewals',
                  self.number_of_circ_operations(lib.pid, 'extend'))
            print('# statisfied ill requests',
                  self.number_of_satisfied_ill_request(lib.pid))

            print('---- Optionals ----')
            print('# items', self.number_of_items(lib.pid))
            print('# new items', self.number_of_new_items(lib.pid))
            print('# deleted items', self.number_of_deleted_items(lib.pid))
            print('# patrons', self.number_of_patrons(lib.organisation.pid))
            print('# new patrons',
                  self.number_of_new_patrons(lib.organisation.pid))
            print('# checkins',
                  self.number_of_circ_operations(lib.pid, 'checkin'))
            print('# requests',
                  self.number_of_circ_operations(lib.pid, 'request'))
            print('')

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
        _to = self.now.format(fmt='YYYY-MM-DDT23:59:59')
        _from = (self.now - relativedelta(months=12))\
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
