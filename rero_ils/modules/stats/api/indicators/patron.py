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

"""Indicator Report Configuration."""


import hashlib

from elasticsearch_dsl.aggs import A

from rero_ils.modules.items.models import ItemCirculationAction
from rero_ils.modules.loans.logs.api import LoanOperationLogsSearch
from rero_ils.modules.locations.api import LocationsSearch
from rero_ils.modules.patrons.api import PatronsSearch
from rero_ils.modules.patrons.models import PatronIdentifier

from .base import IndicatorCfg


class NumberOfPatronsCfg(IndicatorCfg):
    """Number of patrons."""

    @property
    def query(self):
        """Base Elasticsearch Query.

        :returns: an elasticsearch query object
        """
        es_query = PatronsSearch()[:0].filter(
            'term', organisation__pid=self.cfg.org_pid)
        return es_query

    def aggregation(self, distribution):
        """Elasticsearch Aggregation configuration to compute distributions.

        :param distrubtion: str - report distrubtion name
        :returns: an elasticsearch aggregation object
        """
        cfg = {
            'created_month': A(
                'date_histogram',
                field='_created',
                calendar_interval='month',
                format='yyyy-MM'
            ),
            'created_year': A(
                'date_histogram',
                field='_created',
                calendar_interval='year',
                format='yyyy'
            ),
            'birth_year': A(
                'date_histogram',
                field='birth_date',
                calendar_interval='year',
                format='yyyy'
            ),
            'postal_code': A(
                'terms',
                field='postal_code',
                size=self.cfg.aggs_size
            ),
            'gender': A(
                'terms',
                field='gender',
                size=self.cfg.aggs_size
            ),
            'role': A(
                'terms',
                field='roles',
                size=self.cfg.aggs_size
            ),
            'type': A(
                'terms',
                field='patron.type.pid',
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
            'created_month': lambda: bucket.key_as_string,
            'created_year': lambda: bucket.key_as_string,
            'type': lambda:
                f'{self.cfg.patron_types.get(bucket.key, self.label_na_msg)} '
                f'({bucket.key})',
            'birth_year': lambda: bucket.key_as_string,
            'gender': lambda: bucket.key,
            'postal_code': lambda: bucket.key,
            'role': lambda: bucket.key,
        }
        return cfg[distribution]()


class NumberOfActivePatronsCfg(NumberOfPatronsCfg):
    """Number of active patrons."""

    @property
    def query(self):
        """Base Elasticsearch Query.

        :returns: an elasticsearch query object
        """
        es_query = super().query
        range_period = self.cfg.get_range_period(self.cfg.period)
        op_query = LoanOperationLogsSearch()[:0].source()\
            .get_logs_by_trigger(
                triggers=[
                    ItemCirculationAction.EXTEND,
                    ItemCirculationAction.REQUEST,
                    ItemCirculationAction.CHECKIN,
                    ItemCirculationAction.CHECKOUT
                ],
                date_range=range_period)\
            .filter(
                'terms', loan__item__library_pid=self.cfg.lib_pids)
        if lib_pids := self.cfg.filter_by_libraries:
            loc_pids = [
                hit.pid for hit in LocationsSearch().filter(
                    "terms", library__pid=lib_pids).source('pid').scan()]
            op_query = op_query.filter(
                'terms', loan__transaction_location__pid=loc_pids)
        op_query.aggs.bucket('hashed_pid', A(
            'terms',
            field='loan.patron.hashed_pid',
            size=100000
        ))
        results = op_query.execute()
        convert = {
            hashlib.md5(f'{i}'.encode()).hexdigest(): i
            for i in range(1, PatronIdentifier.max() + 1)
        }
        active_patron_pids = [
            convert[v.key] for v in
            results.aggregations.hashed_pid.buckets
        ]
        return es_query.filter('terms', pid=active_patron_pids)
