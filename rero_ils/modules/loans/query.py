# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
# Copyright (C) 2019-2022 UCLouvain
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

"""Query factories for Document REST API."""
from elasticsearch_dsl import Q


def misc_status_filter():
    """Query filter allowing to filter loans using miscellaneous statuses.

    Miscellaneous status are values based on other field :
      - overdue: loans with `end_date` lower than current timestamp.
      - request_expire: loans with a `request_expire_date` lower than current
        timestamp.

    :return: Function allowing to filter the ElasticSearch query.
    """
    def inner(values):
        queries = []
        # OVERDUE
        #   Filter query to return only loans with an `end_date` lower than the
        #   current timestamp.
        if 'overdue' in values:
            queries.append(Q('range', end_date={'lt': 'now/d'}))
        # EXPIRED_REQUEST
        #   Filter query to return only loans with a `request_expire_date`
        #   lower than the current timestamp
        if 'expired_request' in values:
            queries.append(Q('range', request_expire_date={'lt': 'now/d'}))
        return Q('bool', must=queries)
    return inner
