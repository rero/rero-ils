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

"""Utils functions about patron_transaction_events."""
from elasticsearch_dsl import Q
from flask import request
from invenio_records_rest.utils import make_comma_list_a_list

from rero_ils.modules.patron_transaction_events.models import PatronTransactionEventType


def total_facet_filter_builder(search, urlkwargs):
    """Build the filter to use to build 'total' aggregation filter.

    As the configuration of `total` aggregation for patron transaction events
    uses the OR operator, we need to filter this aggregations keeping only
    `payment` event type. Additionally, it's also possible to filter the result
    using event `subtype` (OR operator also used for this filter) ; so all
    selected subtypes must be included into this facet filter.

    :param search: the request search.
    :param urlkwargs: possible url argument from query string (could be empty).
    :return the JSON filter configuration to apply on the facet.
    """
    facet_filter = Q("term", type=PatronTransactionEventType.PAYMENT)
    searched_subtypes = make_comma_list_a_list(request.args.getlist("subtype"))
    if searched_subtypes := [sub.strip() for sub in searched_subtypes]:
        subtypes_query = Q("match_none")  # Initial OR query condition
        for subtype in searched_subtypes:
            subtypes_query |= Q("term", subtype=subtype)
        facet_filter &= subtypes_query
    return facet_filter.to_dict()
