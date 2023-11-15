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

from rero_ils.modules.libraries.api import LibrariesSearch
from rero_ils.modules.locations.api import LocationsSearch
from rero_ils.modules.patron_types.api import PatronTypesSearch
from rero_ils.modules.stats_cfg.api import StatConfiguration
from rero_ils.modules.utils import extracted_data_from_ref

from .indicators import NumberOfActivePatronsCfg, NumberOfCirculationCfg, \
    NumberOfDeletedItemsCfg, NumberOfDocumentsCfg, NumberOfILLRequests, \
    NumberOfItemsCfg, NumberOfPatronsCfg, NumberOfRequestsCfg, \
    NumberOfSerialHoldingsCfg
from ..api.api import Stat
from ..models import StatType


class StatsReport:
    """Statistics for report."""

    def __init__(self, config):
        """Constructor.

        Set variables to create report.
        """
        if not isinstance(config, StatConfiguration):
            config = StatConfiguration(data=config)
        self.config = config
        self.is_active = config.get('is_active', False)
        self.indicator = config['category']['indicator']['type']
        self.period = config['category']['indicator'].get('period')
        self.distributions = config[
            'category']['indicator'].get('distributions', [])
        self.org_pid = config.organisation_pid
        self.filter_by_libraries = []
        for library in config.get('filter_by_libraries', []):
            self.filter_by_libraries.append(extracted_data_from_ref(library))
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

    @property
    def indicator_cfg(self):
        """Indicator configuration.

        :returns: the current indicator configuration.
        :rtype: IndicatorCfg instance.
        """
        cfg = {
            'number_of_documents': NumberOfDocumentsCfg(self),
            'number_of_serial_holdings': NumberOfSerialHoldingsCfg(self),
            'number_of_items': NumberOfItemsCfg(self),
            'number_of_deleted_items': NumberOfDeletedItemsCfg(self),
            'number_of_ill_requests': NumberOfILLRequests(self),
            'number_of_checkins': NumberOfCirculationCfg(self, 'checkin'),
            'number_of_checkouts': NumberOfCirculationCfg(self, 'checkout'),
            'number_of_extends': NumberOfCirculationCfg(self, 'extend'),
            'number_of_requests': NumberOfRequestsCfg(self, 'request'),
            'number_of_validate_requests': NumberOfRequestsCfg(
                self, 'validate_request'),
            'number_of_patrons': NumberOfPatronsCfg(self),
            'number_of_active_patrons': NumberOfActivePatronsCfg(self)
        }
        return cfg[self.indicator]

    def _process_aggregations(self, es_results):
        """Process the es aggregations structures."""
        results = {}
        y_keys = set()
        iter_distrib = iter(self.distributions)
        if distrib1 := next(iter_distrib, None):
            distrib2 = next(iter_distrib, None)
            for dist1 in es_results.aggs[distrib1].buckets:
                if isinstance(dist1, str):
                    key1 = dist1
                    parent_dist = es_results.aggs[distrib1].buckets[key1]
                    doc_count = \
                        es_results.aggs[distrib1].buckets[key1].doc_count
                else:
                    parent_dist = dist1
                    key1 = self.indicator_cfg.label(distrib1, dist1)
                    doc_count = dist1.doc_count
                if not doc_count:
                    continue
                results[key1] = dict(count=doc_count)
                values = {}
                if distrib2:
                    for dist2 in parent_dist[distrib2].buckets:
                        if isinstance(dist2, str):
                            key2 = dist2
                            doc_count = dist1[distrib2].buckets[key2].doc_count
                        else:
                            key2 = self.indicator_cfg.label(distrib2, dist2)
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
        # base query
        search = self.indicator_cfg.query
        # no distributions returns the count
        if not self.distributions:
            return [[search.count()]]

        # distributions
        aggs = search.aggs

        # compute distributions using aggregations
        for dist in self.distributions:
            aggs = aggs.bucket(dist, self.indicator_cfg.aggregation(dist))

        # compute the aggregations using es
        results = search.execute()

        return self._process_aggregations(results)

    def get_range_period(self, period):
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

    def create_stat(self, values, dbcommit=True, reindex=True):
        """Create a stat report.

        :params values: array - value computed by the StatReport class.
        :param dbcommit: bool - if True commit the database transaction.
        :param reindex: bool - if True index the document.
        :returns: the create report.
        """
        data = dict(
                type=StatType.REPORT,
                config=self.config.dumps(),
                values=[dict(results=values)]
            )
        if self.period:
            range = self.get_range_period(self.period)
            data['date_range'] = {
                'from': range['gte'],
                'to': range['lte']
            }
        return Stat.create(data, dbcommit=dbcommit, reindex=reindex)
