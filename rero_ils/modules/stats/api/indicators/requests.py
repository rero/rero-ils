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

"""Circulation Requests Indicator Report Configuration."""


from elasticsearch_dsl.aggs import A

from .circulation import NumberOfCirculationCfg


class NumberOfRequestsCfg(NumberOfCirculationCfg):
    """Number of circulation action based on trigger."""

    def aggregation(self, distribution):
        """Elasticsearch Aggregation configuration to compute distributions.

        :param distrubtion: str - report distrubtion name
        :returns: an elasticsearch aggregation object
        """
        cfg = {
            'pickup_location': A(
                'terms',
                field='loan.pickup_location.pid',
                size=self.cfg.aggs_size
            )
        }
        if agg := cfg.get(distribution):
            return agg
        return super().aggregation(distribution)

    def label(self, distribution, bucket):
        """Column/Raw label transformations.

        :param distribution: str - the report distribution name
        :param bucket: the elasticsearch aggregation bucket
        :returns: the label
        :rtype: str
        """
        cfg = {
            'pickup_location': lambda:
                f'{self.cfg.locations.get(bucket.key, self.label_na_msg)} '
                f'({bucket.key})'
        }
        if label_fn := cfg.get(distribution):
            return label_fn()
        return super().label(distribution=distribution, bucket=bucket)
