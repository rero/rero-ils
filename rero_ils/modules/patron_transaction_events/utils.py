# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Utils functions about patron_transaction_events."""

from flask import current_app
from invenio_search.engine import dsl
from werkzeug.datastructures import MultiDict

from rero_ils.facets import _create_filter_dsl, _facet_filter
from rero_ils.modules.patron_transaction_events.models import PatronTransactionEventType


def total_facet_filter_builder(search, urlkwargs):
    """Build the filter of the `total` aggregation.

    The `total` aggregation sums the payments among the search hits. The
    search engine computes aggregations before applying the post filters,
    and the facets factory only injects them into `terms` and
    `date_histogram` aggregations. The active post filters (event type and
    subtype, owning library and location, category) are therefore added here.

    :param search: the request search.
    :param urlkwargs: possible url argument from query string (could be empty).
    :return the JSON filter configuration to apply on the facet.
    """
    facet_filter = dsl.Q("term", type=PatronTransactionEventType.PAYMENT)
    index = "patron_transaction_events"
    post_filters = current_app.config["RECORDS_REST_FACETS"][index].get("post_filters", {})
    filters, filters_group, _ = _create_filter_dsl(MultiDict(), post_filters)
    if active_post_filters := _facet_filter(index, filters, filters_group, "total", None):
        facet_filter &= active_post_filters
    return facet_filter.to_dict()
