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

"""Base Class for Indicator Configuration."""

from abc import abstractmethod


class IndicatorCfg:
    """Abstract class for the indicator configuration."""

    def __init__(self, report_cfg):
        """Constructor.

        :param report_cfg: StatsReport - the given report configuration
        """
        self.cfg = report_cfg
        self.label_na_msg = 'not available'

    @property
    @abstractmethod
    def query(self):
        """Base Elasticsearch Query.

        :returns: an elasticsearch query object
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def aggregation(self, distribution):
        """Elasticsearch Aggregation configuration to compute distributions.

        :param distrubtion: str - report distrubtion name
        :returns: an elasticsearch aggregation object
        """
        raise NotImplementedError

    @abstractmethod
    def label(self, distribution, bucket):
        """Column/Raw label transformations.

        :param distrubtion: str - the report distrubtion name
        :param bucket: the elasticsearch aggregation bucket
        :returns: the label
        :rtype: str
        """
        raise NotImplementedError
