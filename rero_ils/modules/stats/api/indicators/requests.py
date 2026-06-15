# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Circulation Requests Indicator Report Configuration."""

from elasticsearch_dsl.aggs import A

from .circulation import NumberOfCirculationCfg


class NumberOfRequestsCfg(NumberOfCirculationCfg):
    """Number of circulation action based on trigger."""

    def aggregation(self, distribution):
        """Search index Aggregation configuration to compute distributions.

        :param distrubtion: str - report distrubtion name
        :returns: a search index aggregation object
        """
        cfg = {"pickup_location": A("terms", field="loan.pickup_location.pid", size=self.cfg.aggs_size)}
        if agg := cfg.get(distribution):
            return agg
        return super().aggregation(distribution)

    def label(self, distribution, bucket):
        """Column/Raw label transformations.

        :param distribution: str - the report distribution name
        :param bucket: the search index aggregation bucket
        :returns: the label
        :rtype: str
        """
        cfg = {"pickup_location": lambda: f"{self.cfg.locations.get(bucket.key, self.label_na_msg)} ({bucket.key})"}
        if label_fn := cfg.get(distribution):
            return label_fn()
        return super().label(distribution=distribution, bucket=bucket)
