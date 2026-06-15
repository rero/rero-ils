# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Circulation Indicator Report Configuration."""

import re

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
        """Base search index Query.

        :returns: a search index query object
        """
        search_query = (
            LoanOperationLogsSearch()[:0]
            .filter("terms", loan__item__library_pid=self.cfg.lib_pids)
            .filter("term", record__type="loan")
            .filter("term", loan__trigger=self.trigger)
        )
        if period := self.cfg.period:
            search_query = search_query.filter("range", date=self.cfg.get_range_period(period))
        if lib_pids := self.cfg.filter_by_libraries:
            loc_pids = [
                hit.pid for hit in LocationsSearch().filter("terms", library__pid=lib_pids).source("pid").scan()
            ]
            search_query = search_query.filter("terms", loan__transaction_location__pid=loc_pids)
        return search_query

    def aggregation(self, distribution):
        """Search index Aggregation configuration to compute distributions.

        :param distrubtion: str - report distrubtion name
        :returns: a search index aggregation object
        """
        cfg = {
            "transaction_location": A("terms", field="loan.transaction_location.pid", size=self.cfg.aggs_size),
            "transaction_month": A(
                "date_histogram",
                field="date",
                calendar_interval="month",
                format="yyyy-MM",
            ),
            "transaction_year": A("date_histogram", field="date", calendar_interval="year", format="yyyy"),
            "patron_type": A("terms", field="loan.patron.type", size=self.cfg.aggs_size),
            "patron_age": A("terms", field="loan.patron.age", size=self.cfg.aggs_size),
            "patron_postal_code": A("terms", field="loan.patron.postal_code", size=self.cfg.aggs_size),
            "patron_local_codes": A("terms", field="loan.patron.local_codes", size=self.cfg.aggs_size),
            "document_type": A("terms", field="loan.item.document.type", size=self.cfg.aggs_size),
            "transaction_channel": A("terms", field="loan.transaction_channel", size=self.cfg.aggs_size),
            "owning_library": A("terms", field="loan.item.library_pid", size=self.cfg.aggs_size),
            # Historical logs carry only location_name; newer ones also carry
            # location_pid. Emit "name (pid)" when the pid exists so same-named
            # locations stay distinct, and fall back to the bare name otherwise.
            "owning_location": A(
                "terms",
                script={
                    "source": (
                        "def name = doc['loan.item.holding.location_name.raw'].value;"
                        " def pid = doc['loan.item.holding.location_pid'];"
                        " return pid.size() > 0 ? name + ' (' + pid.value + ')' : name;"
                    ),
                    "lang": "painless",
                },
                size=self.cfg.aggs_size,
            ),
        }
        return cfg[distribution]

    def label(self, distribution, bucket):
        """Column/Raw label transformations.

        :param distrubtion: str - the report distrubtion name
        :param bucket: the search index aggregation bucket
        :returns: the label
        :rtype: str
        """

        def get_owning_location_label(value):

            match = re.match(r"^.*\s\(([^()]+)\)$", value)
            if match:
                location_pid = match.group(1)
                return self.cfg.locations.get(location_pid, value)
            return value

        cfg = {
            "transaction_location": lambda: f"{self.cfg.locations.get(bucket.key, self.label_na_msg)} ({bucket.key})",
            "transaction_month": lambda: bucket.key_as_string,
            "transaction_year": lambda: bucket.key_as_string,
            "patron_type": lambda: bucket.key,
            "patron_age": lambda: bucket.key,
            "document_type": lambda: bucket.key,
            "patron_postal_code": lambda: bucket.key,
            "patron_local_codes": lambda: bucket.key,
            "transaction_channel": lambda: bucket.key,
            "owning_library": lambda: f"{self.cfg.libraries.get(bucket.key, self.label_na_msg)} ({bucket.key})",
            "owning_location": lambda: get_owning_location_label(bucket.key),
        }
        return cfg[distribution]()
