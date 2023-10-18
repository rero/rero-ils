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

"""To compute the statistics for pricing."""

from datetime import datetime

import arrow
from dateutil.relativedelta import relativedelta
from flask import current_app
from invenio_search.api import RecordsSearch

from rero_ils.modules.acquisition.acq_order_lines.api import \
    AcqOrderLinesSearch
from rero_ils.modules.documents.api import DocumentsSearch
from rero_ils.modules.ill_requests.api import ILLRequestsSearch
from rero_ils.modules.ill_requests.models import ILLRequestStatus
from rero_ils.modules.items.api import ItemsSearch
from rero_ils.modules.items.models import ItemCirculationAction
from rero_ils.modules.libraries.api import LibrariesSearch
from rero_ils.modules.loans.logs.api import LoanOperationLogsSearch
from rero_ils.modules.operation_logs.api import OperationLog
from rero_ils.modules.patrons.api import PatronsSearch
from rero_ils.modules.stats.api.api import StatsSearch
from rero_ils.modules.users.models import UserRole


class StatsForPricing:
    """Statistics for pricing."""

    def __init__(self, to_date=None):
        """Constructor.

        :param to_date: end date of the statistics date range
        """
        if to_date and isinstance(to_date, datetime):
            to_date = arrow.Arrow.fromdatetime(to_date)
        to_date = to_date or arrow.utcnow() - relativedelta(days=1)
        self.months_delta = current_app.config.get(
            'RERO_ILS_STATS_BILLING_TIMEFRAME_IN_MONTHS'
        )
        _from = (to_date - relativedelta(
            months=self.months_delta)).format(fmt='YYYY-MM-DDT00:00:00')
        _to = to_date.format(fmt='YYYY-MM-DDT23:59:59')
        self.date_range = {'gte': _from, 'lte': _to}

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
        """Collect all the statistics."""
        stats = []
        for lib in LibrariesSearch().source(
                ['pid', 'name', 'organisation']).scan():
            data = {
                'library': {
                    'pid': lib.pid,
                    'name': lib.name
                }
            }
            data |= self.process(lib)
            stats.append(data)
        return stats

    def process(self, library):
        """Process statistics for a give library.

        :param library: library from the elasticsearch index
        :return: a dict containing all the processed values.
        """
        return {
            'number_of_documents': self.number_of_documents(library.pid),
            'number_of_libraries': self.number_of_libraries(
                library.organisation.pid),
            'number_of_librarians': self.number_of_librarians(library.pid),
            'number_of_active_patrons': self.number_of_active_patrons(
                library.pid),
            'number_of_order_lines': self.number_of_order_lines(library.pid),
            'number_of_checkouts':
                self.number_of_circ_operations(
                    library.pid, ItemCirculationAction.CHECKOUT),
            'number_of_renewals':
                self.number_of_circ_operations(
                    library.pid, ItemCirculationAction.EXTEND),
            'number_of_ill_requests':
                self.number_of_ill_requests(
                    library.pid, [ILLRequestStatus.DENIED]),
            'number_of_items': self.number_of_items(library.pid),
            'number_of_new_items': self.number_of_new_items(library.pid),
            'number_of_deleted_items': self.number_of_deleted_items(
                library.pid),
            'number_of_patrons': self.number_of_patrons(
                library.organisation.pid),
            'number_of_new_patrons': self.number_of_patrons(
                library.organisation.pid),
            'number_of_checkins':
                self.number_of_circ_operations(
                    library.pid,  ItemCirculationAction.CHECKIN),
            'number_of_requests':
                self.number_of_circ_operations(
                    library.pid,  ItemCirculationAction.REQUEST)
        }

    def number_of_documents(self, library_pid):
        """Number of documents linked to my library.

        point in time
        :param library_pid: string - the library to filter with
        :return: the number of matched documents
        :rtype: integer
        """
        return DocumentsSearch().by_library_pid(library_pid).count()

    def number_of_libraries(self, organisation_pid):
        """Number of libraries of the given organisation.

        point in time
        :param organisation_pid: string - the organisation to filter with
        :return: the number of matched libraries
        :rtype: integer
        """
        return LibrariesSearch().by_organisation_pid(organisation_pid).count()

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
        """Number of patrons who did a transaction in the past 365 days.

        :param library_pid: string - the library to filter with
        :return: the number of matched active patrons
        :rtype: integer
        """
        patrons = set()
        op_logs_query = LoanOperationLogsSearch().get_logs_by_trigger(
                triggers=[
                    ItemCirculationAction.CHECKOUT,
                    ItemCirculationAction.EXTEND
                ], date_range=self.date_range
            ).filter('term', loan__item__library_pid=library_pid)
        for res in op_logs_query.source(['loan']).scan():
            patrons.add(res.loan.patron.hashed_pid)
        return len(patrons)

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
        return LoanOperationLogsSearch().get_logs_by_trigger(
                triggers=[trigger],
                date_range=self.date_range
            ).filter('term', loan__item__library_pid=library_pid)\
            .count()

    def number_of_ill_requests(self, library_pid, exclude_status):
        """Number of existing ILL requests for a time range and a library.

        :param library_pid: string - the library to filter with
        :param exclude_status: list of statuses to exclude from the count
        :return: the number of matched inter library loan requests
        :rtype: integer
        """
        query = ILLRequestsSearch()\
            .filter('range', _created=self.date_range)\
            .filter('term', library__pid=library_pid)\
            .exclude('terms', status=exclude_status)
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
        return RecordsSearch(index=OperationLog.index_name)\
            .filter('range', date=self.date_range)\
            .filter('term', operation='delete')\
            .filter('term', record__type='item')\
            .filter('term', library__value=library_pid)\
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
