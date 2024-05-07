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

"""Indicator Report Configurations."""


from elasticsearch_dsl import Q
from elasticsearch_dsl.aggs import A

from rero_ils.modules.documents.api import DocumentsSearch
from rero_ils.modules.holdings.api import HoldingsSearch
from rero_ils.modules.ill_requests.api import ILLRequestsSearch
from rero_ils.modules.items.api import ItemsSearch
from rero_ils.modules.loans.logs.api import LoanOperationLogsSearch

from .base import IndicatorCfg


class NumberOfDocumentsCfg(IndicatorCfg):
    """Number of Documents."""

    @property
    def query(self):
        """Base Elasticsearch Query.

        :returns: an elasticsearch query object
        """
        es_query = DocumentsSearch()[:0].filter(
            'term',
            organisation_pid=self.cfg.org_pid
        )
        if pids := self.cfg.filter_by_libraries:
            es_query = es_query.filter(
                'terms', library_pid=pids)
        return es_query

    def aggregation(self, distribution):
        """Elasticsearch Aggregation configuration to compute distributions.

        :param distrubtion: str - report distribution name
        :returns: an elasticsearch aggregation object
        """
        cfg = {
            'owning_library': A(
                'terms',
                field='holdings.organisation.library_pid',
                size=self.cfg.aggs_size,
                include=self.cfg.lib_pids
            ),
            'created_month': A(
                'date_histogram',
                field='_created',
                calendar_interval='month',
                format='yyyy-MM'
            ),
            'created_year': A(
                'date_histogram', field='_created',
                calendar_interval='year', format='yyyy'
            ),
            'imported': A(
                'filters', other_bucket_key="not imported",
                filters={
                    'imported': {
                        'exists': {'field': 'adminMetadata.source'}
                    }
                }
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
            'owning_library': lambda:
                f'{self.cfg.libraries.get(bucket.key, self.label_na_msg)} '
                f'({bucket.key})',
            'created_month': lambda: bucket.key_as_string,
            'created_year': lambda: bucket.key_as_string,
            'imported': lambda: bucket
        }
        return cfg[distribution]()


class NumberOfSerialHoldingsCfg(IndicatorCfg):
    """Number of serial holdings."""

    @property
    def query(self):
        """Base Elasticsearch Query.

        :returns: an elasticsearch query object
        """
        es_query = HoldingsSearch()[:0]\
            .filter('term', holdings_type='serial')\
            .filter('term', organisation__pid=self.cfg.org_pid)
        if pids := self.cfg.filter_by_libraries:
            es_query = es_query.filter(
                'terms', library__pid=pids)
        return es_query

    def aggregation(self, distribution):
        """Elasticsearch Aggregation configuration to compute distributions.

        :param distrubtion: str - report distrubtion name
        :returns: an elasticsearch aggregation object
        """
        cfg = {
            'owning_library': A(
                'terms',
                field='library.pid',
                size=self.cfg.aggs_size,
                include=self.cfg.lib_pids
            ),
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
            'owning_library': lambda:
                f'{self.cfg.libraries.get(bucket.key, self.label_na_msg)} '
                f'({bucket.key})',
            'created_month': lambda: bucket.key_as_string,
            'created_year': lambda: bucket.key_as_string
        }
        return cfg[distribution]()


class NumberOfItemsCfg(IndicatorCfg):
    """Number of items."""

    @property
    def query(self):
        """Base Elasticsearch Query.

        :returns: an elasticsearch query object
        """
        es_query = ItemsSearch()[:0].filter(
            'term', organisation__pid=self.cfg.org_pid)
        if pids := self.cfg.filter_by_libraries:
            es_query = es_query.filter(
                'terms', library__pid=pids)
        return es_query

    def aggregation(self, distribution):
        """Elasticsearch Aggregation configuration to compute distributions.

        :param distrubtion: str - report distrubtion name
        :returns: an elasticsearch aggregation object
        """
        cfg = {
            'owning_library': A(
                'terms',
                field='library.pid',
                size=self.cfg.aggs_size,
                include=self.cfg.lib_pids
            ),
            'owning_location': A(
                'terms',
                field='location.pid',
                size=self.cfg.aggs_size,
                include=self.cfg.loc_pids
            ),
            'type': A(
                'terms',
                field='type',
                size=self.cfg.aggs_size
            ),
            'document_type': A(
                'terms',
                field='document.document_type.main_type',
                size=self.cfg.aggs_size
            ),
            'document_subtype': A(
                'terms',
                field='document.document_type.subtype',
                size=self.cfg.aggs_size
            ),
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
            'owning_library': lambda:
                f'{self.cfg.libraries.get(bucket.key, self.label_na_msg)} '
                f'({bucket.key})',
            'owning_location': lambda:
                f'{self.cfg.locations.get(bucket.key, self.label_na_msg)} '
                f'({bucket.key})',
            'type': lambda: bucket.key,
            'document_type': lambda: bucket.key,
            'document_subtype': lambda: bucket.key,
            'created_month': lambda: bucket.key_as_string,
            'created_year': lambda: bucket.key_as_string
        }
        return cfg[distribution]()


class NumberOfDeletedItemsCfg(IndicatorCfg):
    """Number of deleted items."""

    @property
    def query(self):
        """Base Elasticsearch Query.

        :returns: an elasticsearch query object
        """
        es_query = (
            LoanOperationLogsSearch()[:0]
            .filter(
                Q("term", record__organisation_pid=self.cfg.org_pid)
                | Q("term", organisation__value=self.cfg.org_pid)
            )
            .filter("term", record__type="item")
            .filter("term", operation="delete")
        )
        if period := self.cfg.period:
            es_query = es_query.filter(
                "range", date=self.cfg.get_range_period(period))
        if pids := self.cfg.filter_by_libraries:
            es_query = es_query.filter(
                Q("terms", record__library_pid=pids)
                | Q("terms", library__value=pids)
            )
        return es_query

    def aggregation(self, distribution):
        """Elasticsearch Aggregation configuration to compute distributions.

        :param distrubtion: str - report distrubtion name
        :returns: an elasticsearch aggregation object
        """
        cfg = {
            'owning_library': A(
                'terms',
                field='record.library_pid',
                size=self.cfg.aggs_size
            ),
            "operator_library": A(
                "terms",
                field="library.value",
                size=self.cfg.aggs_size
            ),
            "action_month": A(
                "date_histogram",
                field="date",
                calendar_interval="month",
                format="yyyy-MM",
            ),
            "action_year": A(
                "date_histogram",
                field="date",
                calendar_interval="year",
                format="yyyy"
            ),
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
            "owning_library": lambda:
                f"{self.cfg.libraries.get(bucket.key, self.label_na_msg)} "
                f"({bucket.key})",
            "operator_library": lambda:
                f"{self.cfg.libraries.get(bucket.key, self.label_na_msg)} "
                f"({bucket.key})",
            "action_month": lambda: bucket.key_as_string,
            "action_year": lambda: bucket.key_as_string,
        }
        return cfg[distribution]()


class NumberOfILLRequests(IndicatorCfg):
    """Number of ill requests."""

    @property
    def query(self):
        """Base Elasticsearch Query.

        :returns: an elasticsearch query object
        """
        es_query = ILLRequestsSearch()[:0].filter(
            'term', organisation__pid=self.cfg.org_pid)
        if period := self.cfg.period:
            es_query = es_query.filter(
                'range', _created=self.cfg.get_range_period(period))
        if pids := self.cfg.filter_by_libraries:
            es_query = es_query.filter(
                'terms', library__pid=pids)
        return es_query

    def aggregation(self, distribution):
        """Elasticsearch Aggregation configuration to compute distributions.

        :param distrubtion: str - report distrubtion name
        :returns: an elasticsearch aggregation object
        """
        cfg = {
            'pickup_location': A(
                'terms',
                field='pickup_location.pid',
                size=self.cfg.aggs_size
            ),
            'status': A(
                'terms',
                field='status',
                size=self.cfg.aggs_size
            ),
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
            'pickup_location': lambda:
                f'{self.cfg.locations.get(bucket.key, self.label_na_msg)} '
                f'({bucket.key})',
            'status': lambda: bucket.key,
            'created_month': lambda: bucket.key_as_string,
            'created_year': lambda: bucket.key_as_string
        }
        return cfg[distribution]()
