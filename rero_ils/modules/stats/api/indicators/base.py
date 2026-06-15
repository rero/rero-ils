# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Base Class for Indicator Configuration."""

from abc import abstractmethod


class IndicatorCfg:
    """Abstract class for the indicator configuration."""

    def __init__(self, report_cfg):
        """Constructor.

        :param report_cfg: StatsReport - the given report configuration
        """
        self.cfg = report_cfg
        self.label_na_msg = "not available"

    @property
    @abstractmethod
    def query(self):
        """Base search index Query.

        :returns: a search index query object
        """
        raise NotImplementedError()

    @property
    @abstractmethod
    def aggregation(self, distribution):
        """Search index Aggregation configuration to compute distributions.

        :param distrubtion: str - report distrubtion name
        :returns: a search index aggregation object
        """
        raise NotImplementedError()

    @abstractmethod
    def label(self, distribution, bucket):
        """Column/Raw label transformations.

        :param distrubtion: str - the report distrubtion name
        :param bucket: the search index aggregation bucket
        :returns: the label
        :rtype: str
        """
        raise NotImplementedError()
