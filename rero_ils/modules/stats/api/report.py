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

"""To compute the statistics from configuration."""

from datetime import datetime

from dateutil.relativedelta import relativedelta
from elasticsearch_dsl.aggs import A
from invenio_search.api import RecordsSearch

from rero_ils.modules.documents.api import DocumentsSearch
from rero_ils.modules.holdings.api import HoldingsSearch
from rero_ils.modules.ill_requests.api import ILLRequestsSearch
from rero_ils.modules.items.api import ItemsSearch
from rero_ils.modules.items.models import ItemCirculationAction
from rero_ils.modules.libraries.api import LibrariesSearch
from rero_ils.modules.loans.logs.api import LoanOperationLog, \
    LoanOperationLogsSearch
from rero_ils.modules.locations.api import LocationsSearch
from rero_ils.modules.patron_types.api import PatronTypesSearch
from rero_ils.modules.patrons.api import PatronsSearch
from rero_ils.modules.utils import extracted_data_from_ref


class StatsReport:
    """Statistics for report."""

    def __init__(self, config):
        """Constructor.

        Set variables to create report.
        """
        self.config = config
        self.is_active = config.get('is_active', False)
        self.indicator = config['category']['indicator']['type']
        self.period = config['category']['indicator'].get('period')
        self.distributions = config[
            'category']['indicator'].get('distributions', [])
        self.org_pid = extracted_data_from_ref(config['organisation'])
        self.libraries = {
            hit.pid: hit.name for hit in LibrariesSearch().by_organisation_pid(
                self.org_pid).source(['pid', 'name']).scan()
        }
        self.lib_pids = list(self.libraries.keys())
        es_locations = LocationsSearch().by_organisation_pid(
                self.org_pid).source(['pid', 'name', 'library']).scan()
        self.locations = {
            hit.pid: f'{self.libraries[hit.library.pid]} / {hit.name}'
            for hit in es_locations
        }
        self.patron_types = {
            hit.pid: hit.name for hit in
            PatronTypesSearch().by_organisation_pid(
                self.org_pid).source(['pid', 'name']).scan()
        }
        self.loc_pids = list(self.locations.keys())
        self.aggs_size = 10000
        self.es_config = {
            'number_of_documents': {
                'query': lambda: DocumentsSearch()[:0].filter(
                    'term',
                    holdings__organisation__organisation_pid=self.org_pid
                ),
                'aggs': {
                    'library': lambda: A(
                        'terms', field='holdings.organisation.library_pid',
                        size=self.aggs_size, include=self.lib_pids
                    ),
                    'created_month': lambda: A(
                        'date_histogram', field='_created',
                        calendar_interval='month', format='yyyy-MM'
                    ),
                    'created_year': lambda: A(
                        'date_histogram', field='_created',
                        calendar_interval='year', format='yyyy'
                    ),
                    'imported': lambda: A(
                        'filters', other_bucket_key="not imported",
                        filters={'imported': {
                            'exists': {'field': 'adminMetadata.source'}}}
                    )
                },
                'get_key': {
                    'library': lambda bucket:
                        f'{self.libraries[bucket.key]} ({bucket.key})',
                    'created_month': lambda bucket: bucket.key_as_string,
                    'created_year': lambda bucket: bucket.key_as_string,
                    'imported': lambda bucket: bucket
                }
            },
            'number_of_serial_holdings': {
                'query': lambda: HoldingsSearch()[:0]
                .filter('term', holdings_type='serial')
                .filter('term', organisation__pid=self.org_pid),
                'aggs': {
                    'library': lambda: A(
                        'terms', field='library.pid', size=self.aggs_size,
                        include=self.lib_pids),
                    'created_month': lambda: A(
                        'date_histogram', field='_created',
                        calendar_interval='month', format='yyyy-MM'),
                    'created_year': lambda: A(
                        'date_histogram', field='_created',
                        calendar_interval='year', format='yyyy')
                },
                'get_key': {
                    'library': lambda bucket:
                    f'{self.libraries[bucket.key]} ({bucket.key})',
                    'created_month': lambda bucket: bucket.key_as_string,
                    'created_year': lambda bucket: bucket.key_as_string
                }
            },
            'number_of_items': {
                'query': lambda: ItemsSearch()[:0].filter(
                    'term', organisation__pid=self.org_pid
                ),
                'aggs': {
                    'library': lambda: A(
                        'terms', field='library.pid', size=self.aggs_size,
                        include=self.lib_pids),
                    'location': lambda: A(
                        'terms', field='location.pid', size=self.aggs_size,
                        include=self.loc_pids),
                    'type': lambda: A(
                        'terms', field='type', size=self.aggs_size),
                    'created_month': lambda: A(
                        'date_histogram', field='_created',
                        calendar_interval='month', format='yyyy-MM'),
                    'created_year': lambda: A(
                        'date_histogram', field='_created',
                        calendar_interval='year', format='yyyy')
                },
                'get_key': {
                    'library': lambda bucket:
                    f'{self.libraries[bucket.key]} ({bucket.key})',
                    'location': lambda bucket:
                    f'{self.locations[bucket.key]} ({bucket.key})',
                    'type': lambda bucket: bucket.key,
                    'created_month': lambda bucket:
                    bucket.key_as_string,
                    'created_year': lambda bucket:
                    bucket.key_as_string
                },
            },
            'number_of_ill_requests': {
                'query': lambda: (s := ILLRequestsSearch()[:0].filter(
                    'term', organisation__pid=self.org_pid),
                    s.filter(
                        'range', _created=self._get_range_period(self.period))
                    )[self.period is not None],
                'aggs': {
                    'pickup_location': lambda: A(
                        'terms', field='pickup_location.pid',
                        size=self.aggs_size),
                    'status': lambda: A(
                        'terms', field='status', size=self.aggs_size),
                    'created_month': lambda: A(
                        'date_histogram', field='_created',
                        calendar_interval='month', format='yyyy-MM'),
                    'created_year': lambda: A(
                        'date_histogram', field='_created',
                        calendar_interval='year', format='yyyy')
                },
                'get_key': {
                    'pickup_location': lambda bucket:
                    f'{self.locations[bucket.key]} ({bucket.key})',
                    'status': lambda bucket: bucket.key,
                    'created_month': lambda bucket:
                    bucket.key_as_string,
                    'created_year': lambda bucket:
                    bucket.key_as_string
                }
            },
            'number_of_deleted_items': {
                'query': lambda: (
                    s := RecordsSearch(index=LoanOperationLog.index_name)[:0]
                    .filter('term', organisation__value=self.org_pid)
                    .filter('term', record__type='item')
                    .filter('term', operation='delete'),
                    s.filter('range', date=self._get_range_period(self.period))
                )[self.period is not None],
                'aggs': {
                    'library': lambda: A(
                        'terms', field='library.value', size=self.aggs_size),
                    'action_month': lambda: A(
                        'date_histogram', field='date',
                        calendar_interval='month', format='yyyy-MM'),
                    'action_year': lambda: A(
                        'date_histogram', field='date',
                        calendar_interval='year', format='yyyy')
                },
                'get_key': {
                    'library': lambda bucket:
                    f'{self.libraries[bucket.key]} ({bucket.key})',
                    'action_month': lambda bucket: bucket.key_as_string,
                    'action_year': lambda bucket: bucket.key_as_string
                }
            },
            'number_of_checkins': self._circulation_config('checkin'),
            'number_of_checkouts': self._circulation_config('checkout'),
            'number_of_extends': self._circulation_config('extend'),
            'number_of_requests': self._circulation_config('request'),
            'number_of_validate_requests':
            self._circulation_config('validate_request'),
            'number_of_patrons': self._patron_config(active=False),
            'number_of_active_patrons': self._patron_config(active=True),
        }

    def _patron_config(self, active):
        """The es configuration for patron indicators."""
        patron_cfg = {
            'aggs': {
                'created_month': lambda: A(
                    'date_histogram', field='_created',
                    calendar_interval='month', format='yyyy-MM'
                ),
                'created_year': lambda: A(
                    'date_histogram', field='_created',
                    calendar_interval='year', format='yyyy'
                ),
                'birth_year': lambda: A(
                    'date_histogram', field='birth_date',
                    calendar_interval='year', format='yyyy'
                ),
                'postal_code': lambda: A(
                    'terms', field='postal_code', size=self.aggs_size),
                'gender': lambda: A(
                    'terms', field='gender', size=self.aggs_size),
                'role': lambda: A(
                    'terms', field='roles', size=self.aggs_size),
                'type': lambda: A(
                    'terms', field='patron.type.pid', size=self.aggs_size),
            },
            'get_key': {
                'created_month': lambda bucket: bucket.key_as_string,
                'created_year': lambda bucket: bucket.key_as_string,
                'type': lambda bucket:
                f'{self.patron_types[bucket.key]} ({bucket.key})',
                'birth_year': lambda bucket: bucket.key_as_string,
                'gender': lambda bucket: bucket.key,
                'postal_code': lambda bucket: bucket.key,
                'role': lambda bucket: bucket.key,
            }
        }
        base_query = PatronsSearch()[:0].filter(
            'term', organisation__pid=self.org_pid)

        if active:
            def active_patron_query():
                """The based patron query and filter by active pid."""
                range_period = self._get_range_period(self.period)
                active_patron_pids = [
                    hit.loan.patron.pid for hit in LoanOperationLogsSearch()
                    .source('loan.patron.pid')
                    .get_logs_by_trigger(
                        triggers=[
                            ItemCirculationAction.EXTEND,
                            ItemCirculationAction.REQUEST,
                            ItemCirculationAction.CHECKIN,
                            ItemCirculationAction.CHECKOUT
                        ],
                        date_range=range_period)
                    .filter(
                        'terms', loan__item__library_pid=self.lib_pids).scan()
                ]
                return base_query.filter('terms', pid=active_patron_pids)

            patron_cfg['query'] = active_patron_query
        else:
            patron_cfg['query'] = lambda: base_query
        return patron_cfg

    def _circulation_config(self, trigger):
        """The es configuration for circulation indicators."""
        return {
            # here two cases should be considered depending of the existence of
            # self.period, the lambda function create a tuple of two values and
            # return the first or the second based on the index of the tuple
            # 0 if not period else 1 as a boolean is an integer
            'query': lambda: (
                s := RecordsSearch(index=LoanOperationLog.index_name)[:0]
                .filter('terms', loan__item__library_pid=self.lib_pids)
                .filter('term', record__type='loan')
                .filter('term', loan__trigger=trigger),
                s.filter('range', date=self._get_range_period(self.period))
            )[self.period is not None],
            'aggs': {
                'transaction_location': lambda: A(
                    'terms', field='loan.transaction_location.pid',
                    size=self.aggs_size),
                'transaction_month': lambda: A(
                    'date_histogram', field='date',
                    calendar_interval='month', format='yyyy-MM'),
                'transaction_year': lambda: A(
                    'date_histogram', field='date',
                    calendar_interval='year', format='yyyy'),
                'patron_type': lambda: A(
                    'terms', field='loan.patron.type', size=self.aggs_size),
                'patron_age': lambda: A(
                    'terms', field='loan.patron.age', size=self.aggs_size),
                'patron_type': lambda: A(
                    'terms', field='loan.patron.type', size=self.aggs_size),
                'patron_postal_code': lambda: A(
                    'terms', field='loan.patron.postal_code',
                    size=self.aggs_size),
                'document_type': lambda: A(
                    'terms', field='loan.item.document.type',
                    size=self.aggs_size),
                'transaction_channel': lambda: A(
                    'terms', field='loan.transaction_channel',
                    size=self.aggs_size),
                'owning_library': lambda: A(
                    'terms', field='loan.item.library_pid',
                    size=self.aggs_size)
            },
            'get_key': {
                'transaction_location': lambda bucket:
                f'{self.locations[bucket.key]} ({bucket.key})',
                'transaction_month': lambda bucket: bucket.key_as_string,
                'transaction_year': lambda bucket: bucket.key_as_string,
                'patron_type': lambda bucket: bucket.key,
                'patron_age': lambda bucket: bucket.key,
                'document_type': lambda bucket: bucket.key,
                'patron_postal_code': lambda bucket: bucket.key,
                'transaction_channel': lambda bucket: bucket.key,
                'owning_library': lambda bucket:
                f'{self.libraries[bucket.key]} ({bucket.key})'
            }
        }

    def _process_aggregations(self, es_results):
        """Process the es aggregations structures."""
        cfg = self.es_config.get(self.indicator)
        results = {}
        y_keys = set()
        iter_distrib = iter(self.distributions)
        if distrib1 := next(iter_distrib, None):
            distrib2 = next(iter_distrib, None)
            get_key1 = cfg['get_key'][distrib1]
            for dist1 in es_results.aggs[distrib1].buckets:
                if isinstance(dist1, str):
                    key1 = dist1
                    parent_dist = es_results.aggs[distrib1].buckets[key1]
                    doc_count = \
                        es_results.aggs[distrib1].buckets[key1].doc_count
                else:
                    parent_dist = dist1
                    key1 = get_key1(dist1)
                    doc_count = dist1.doc_count
                if not doc_count:
                    continue
                results[key1] = dict(count=doc_count)
                values = {}
                if distrib2:
                    get_key2 = cfg['get_key'][distrib2]
                    for dist2 in parent_dist[distrib2].buckets:
                        if isinstance(dist2, str):
                            key2 = dist2
                            doc_count = dist1[distrib2].buckets[key2].doc_count
                        else:
                            key2 = get_key2(dist2)
                            doc_count = dist2.doc_count
                        values[key2] = doc_count
                        y_keys.add(key2)
                if values:
                    results[key1]['values'] = values
            y_keys = sorted(y_keys)
            x_keys = sorted(results.keys())
        return self._process_distributions(x_keys, y_keys, results)

    def _process_distributions(self, x_keys, y_keys, results):
        """Process the elasticsearch aggregations results."""
        data = []
        if y_keys:
            data.append([''] + y_keys)

        for x_key in x_keys:
            values = [x_key]
            if y_keys:
                for y_key in y_keys:
                    values.append(
                        results[x_key].get('values', {}).get(y_key, 0))
            else:
                values.append(results[x_key].get('count', 0))
            data.append(values)
        return data

    def collect(self, force=False):
        """Collect data for report.

        :param force: compute even if the configuration is not active.
        :returns: results data of report
        """
        if not self.is_active and not force:
            return
        cfg = self.es_config.get(self.indicator)
        # base query
        search = cfg['query']()
        # no distributions returns the count
        if not self.distributions:
            return [[search.count()]]

        # distributions
        aggs = search.aggs

        # compute distributions using aggregations
        for dist in self.distributions:
            aggs = aggs.bucket(dist, cfg['aggs'][dist]())

        # compute the aggregations using es
        results = search.execute()

        return self._process_aggregations(results)

    def _get_range_period(self, period):
        """Get the range period for elasticsearch date range aggs."""
        if period == 'month':
            # now - 1 month
            previous_month = datetime.now() - relativedelta(months=1)
            # get last day of previous month using relativedelta with
            # day=31: this will add a max value of 31 days but stays
            # in the same month
            previous_month = previous_month + relativedelta(day=31)
            month = '%02d' % previous_month.month
            _from = f'{previous_month.year}-{month}-01T00:00:00'
            _to = f'{previous_month.year}-{month}-{previous_month.day}'
            _to = f'{_to}T23:59:59'
            return dict(gte=_from, lte=_to)
        elif period == 'year':
            previous_year = datetime.now().year - 1
            _from = f'{previous_year}-01-01T00:00:00'
            _to = f'{previous_year}-12-31T23:59:59'
            return dict(gte=_from, lte=_to)
