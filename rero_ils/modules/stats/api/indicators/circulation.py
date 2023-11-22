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

"""Circulation Indicator Report Configuration."""


from elasticsearch_dsl.aggs import A

from rero_ils.modules.loans.logs.api import LoanOperationLogsSearch
from rero_ils.modules.locations.api import LocationsSearch

from .base import IndicatorCfg


class NumberOfCirculationCfg(IndicatorCfg):
    """Number of circulation action based on trigger."""

    def __init__(self, report_cfg, trigger):
        """Constructor.

        :param report_cfg: StatsReport - the given report configuration
        :trigger: str - circulation trigger
        """
        self.trigger = trigger
        super().__init__(report_cfg)

    @property
    def query(self):
        """Base Elasticsearch Query.

        :returns: an elasticsearch query object
        """
        es_query = LoanOperationLogsSearch()[:0]\
            .filter('terms', loan__item__library_pid=self.cfg.lib_pids)\
            .filter('term', record__type='loan')\
            .filter('term', loan__trigger=self.trigger)
        if period := self.cfg.period:
            es_query = es_query.filter(
                'range', date=self.cfg.get_range_period(period))
        if lib_pids := self.cfg.filter_by_libraries:
            loc_pids = [
                hit.pid for hit in LocationsSearch().filter(
                    "terms", library__pid=lib_pids).source('pid').scan()]
            es_query = es_query.filter(
                'terms', loan__transaction_location__pid=loc_pids)
        return es_query

    def aggregation(self, distribution):
        """Elasticsearch Aggregation configuration to compute distributions.

        :param distrubtion: str - report distrubtion name
        :returns: an elasticsearch aggregation object
        """
        cfg = {
            'transaction_location': A(
                'terms',
                field='loan.transaction_location.pid',
                size=self.cfg.aggs_size
            ),
            'transaction_month': A(
                'date_histogram',
                field='date',
                calendar_interval='month',
                format='yyyy-MM'
            ),
            'transaction_year': A(
                'date_histogram',
                field='date',
                calendar_interval='year',
                format='yyyy'
            ),
            'patron_type': A(
                'terms',
                field='loan.patron.type',
                size=self.cfg.aggs_size
            ),
            'patron_age': A(
                'terms',
                field='loan.patron.age',
                size=self.cfg.aggs_size
            ),
            'patron_type': A(
                'terms',
                field='loan.patron.type',
                size=self.cfg.aggs_size
            ),
            'patron_postal_code': A(
                'terms',
                field='loan.patron.postal_code',
                size=self.cfg.aggs_size
            ),
            'document_type': A(
                'terms',
                field='loan.item.document.type',
                size=self.cfg.aggs_size
            ),
            'transaction_channel': A(
                'terms',
                field='loan.transaction_channel',
                size=self.cfg.aggs_size
            ),
            'owning_library': A(
                'terms',
                field='loan.item.library_pid',
                size=self.cfg.aggs_size
            ),
            'owning_location': A(
                'terms',
                field='loan.item.holding.location_name.raw',
                size=self.cfg.aggs_size
            )
        }
        return cfg[distribution]

    def label(self, distribution, bucket):
        """Column/Raw label transformations.

        :param distrubtion: str - the report distrubtion name
        :param bucket: the elasticsearch aggregation bucket
        :returns: the label
        :rtype: str
        """
        cfg = {
            'transaction_location': lambda:
                f'{self.cfg.locations.get(bucket.key, self.label_na_msg)} '
                f'({bucket.key})',
            'transaction_month': lambda: bucket.key_as_string,
            'transaction_year': lambda: bucket.key_as_string,
            'patron_type': lambda: bucket.key,
            'patron_age': lambda: bucket.key,
            'document_type': lambda: bucket.key,
            'patron_postal_code': lambda: bucket.key,
            'transaction_channel': lambda: bucket.key,
            'owning_library': lambda:
                f'{self.cfg.libraries.get(bucket.key, self.label_na_msg)} '
                f'({bucket.key})',
            'owning_location': lambda: bucket.key,
        }
        return cfg[distribution]()
