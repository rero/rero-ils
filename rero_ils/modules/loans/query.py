# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

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
        if "overdue" in values:
            queries.append(Q("range", end_date={"lt": "now/d"}))
        # EXPIRED_REQUEST
        #   Filter query to return only loans with a `request_expire_date`
        #   lower than the current timestamp
        if "expired_request" in values:
            queries.append(Q("range", request_expire_date={"lt": "now/d"}))
        return Q("bool", must=queries)

    return inner
