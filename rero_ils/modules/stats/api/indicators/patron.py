# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

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
        """Base search index Query.

        :returns: a search index query object
        """
        return PatronsSearch()[:0].filter("term", organisation__pid=self.cfg.org_pid)

    def aggregation(self, distribution):
        """Search index Aggregation configuration to compute distributions.

        :param distrubtion: str - report distrubtion name
        :returns: a search index aggregation object
        """
        cfg = {
            "created_month": A(
                "date_histogram",
                field="_created",
                calendar_interval="month",
                format="yyyy-MM",
            ),
            "created_year": A(
                "date_histogram",
                field="_created",
                calendar_interval="year",
                format="yyyy",
            ),
            "birth_year": A(
                "date_histogram",
                field="birth_date",
                calendar_interval="year",
                format="yyyy",
            ),
            "postal_code": A("terms", field="postal_code", size=self.cfg.aggs_size),
            "local_codes": A("terms", field="local_codes", size=self.cfg.aggs_size),
            "gender": A("terms", field="gender", size=self.cfg.aggs_size),
            "role": A("terms", field="roles", size=self.cfg.aggs_size),
            "type": A("terms", field="patron.type.pid", size=self.cfg.aggs_size),
        }
        return cfg[distribution]

    def label(self, distribution, bucket):
        """Column/Raw label transformations.

        :param distrubtion: str - the report distrubtion name
        :param bucket: the search index aggregation bucket
        :returns: the label
        :rtype: str
        """
        cfg = {
            "created_month": lambda: bucket.key_as_string,
            "created_year": lambda: bucket.key_as_string,
            "type": lambda: f"{self.cfg.patron_types.get(bucket.key, self.label_na_msg)} ({bucket.key})",
            "birth_year": lambda: bucket.key_as_string,
            "gender": lambda: bucket.key,
            "postal_code": lambda: bucket.key,
            "local_codes": lambda: bucket.key,
            "role": lambda: bucket.key,
        }
        return cfg[distribution]()


class NumberOfActivePatronsCfg(NumberOfPatronsCfg):
    """Number of active patrons."""

    @property
    def query(self):
        """Base search index Query.

        :returns: a search index query object
        """
        search_query = super().query
        range_period = self.cfg.get_range_period(self.cfg.period)
        op_query = (
            LoanOperationLogsSearch()[:0]
            .source()
            .get_logs_by_trigger(
                triggers=[
                    ItemCirculationAction.EXTEND,
                    ItemCirculationAction.REQUEST,
                    ItemCirculationAction.CHECKIN,
                    ItemCirculationAction.CHECKOUT,
                ],
                date_range=range_period,
            )
            .filter("terms", loan__item__library_pid=self.cfg.lib_pids)
        )
        if lib_pids := self.cfg.filter_by_libraries:
            loc_pids = [
                hit.pid for hit in LocationsSearch().filter("terms", library__pid=lib_pids).source("pid").scan()
            ]
            op_query = op_query.filter("terms", loan__transaction_location__pid=loc_pids)
        op_query.aggs.bucket("hashed_pid", A("terms", field="loan.patron.hashed_pid", size=100000))
        results = op_query.execute()
        convert = {hashlib.md5(f"{i}".encode()).hexdigest(): i for i in range(1, PatronIdentifier.max() + 1)}
        active_patron_pids = [convert[v.key] for v in results.aggregations.hashed_pid.buckets]
        return search_query.filter("terms", pid=active_patron_pids)
