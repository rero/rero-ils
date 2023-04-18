# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
# Copyright (C) 2020 UCLOUVAIN
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

"""Facets and factories for result aggregation."""

from __future__ import absolute_import, print_function

from copy import deepcopy

from elasticsearch_dsl import Q
from flask import current_app, request
from invenio_base.utils import obj_or_import_string
from invenio_i18n.ext import current_i18n
from invenio_records_rest.facets import _aggregations, _query_filter
from invenio_records_rest.utils import make_comma_list_a_list
from six import text_type
from werkzeug.datastructures import MultiDict


def default_facets_factory(search, index):
    """Add a default facets to query.

    It's possible to select facets which should be added to query
    by passing their name in `facets` parameter.

    :param search: Basic search object.
    :param index: Index name.
    :returns: A tuple containing the new search object and a dictionary with
        all fields and values used.
    """
    urlkwargs = MultiDict()
    # Check if facets configuration are defined for this index. If not, then we
    # can't build any facets for this index, just return the current search.
    if index not in current_app.config.get('RECORDS_REST_FACETS', {}):
        return search, urlkwargs

    facets = current_app.config['RECORDS_REST_FACETS'].get(index)
    all_aggs, aggs = facets.get('aggs', {}), {}

    # i18n aggregations.
    #   some aggregations' configuration are different depending on language
    #   use for the search. Load the correct configuration for these
    #   aggregations.
    interface_language = request.args.get('lang', current_i18n.language)
    default_language = current_app.config.get('BABEL_DEFAULT_LANGUAGE')
    for facet_name, facet_body in facets.get("i18n_aggs", {}).items():
        aggr = facet_body.get(interface_language,
                              facet_body.get(default_language))
        all_aggs[facet_name] = aggr

    # Get selected facets
    #   We need to know which facets are needed to be build. User can use the
    #   'facets' query string argument to determine which facets it wants to be
    #   built. If this argument isn't defined, all facets defined into the
    #   configuration will be built.
    selected_facets = request.args.getlist('facets') or all_aggs.keys()
    selected_facets = make_comma_list_a_list(selected_facets)

    # Filter to keep only configuration about selected facets.
    all_aggs = {k: v for k, v in all_aggs.items() if k in selected_facets}

    # Go through all available facets and check if they were requested.
    for facet_name, facet_body in all_aggs.items():
        # be sure that the config still untouched
        facet_body = deepcopy(facet_body)
        # get facet key depending on the aggregation configuration.
        # If no facet field are found, skip this aggregation, because we can't
        # determine which field used to filter the query
        facet_field = next(
            (facet_body.get(k)['field']
             for k in ['terms', 'date_histogram']
             if k in facet_body),
            None
        )
        facet_filter = None
        if facet_field:
            # get DSL expression of post_filters,
            # both single post filters and group of post filters
            filters, filters_group, urlkwargs = _create_filter_dsl(
                urlkwargs,
                facets.get('post_filters', {})
            )
            # create the filter to inject in the facet
            facet_filter = _facet_filter(
                index, filters, filters_group, facet_name, facet_field
            )

        # Check if 'filter' is defined into the facet configuration. If yes,
        # then add this filter to the facet filter previously created.
        if 'filter' in facet_body:
            agg_filter = obj_or_import_string(facet_body.pop('filter'))
            if callable(agg_filter):
                agg_filter = agg_filter(search, urlkwargs)
            if facet_filter:
                facet_filter &= Q(agg_filter)
            else:
                facet_filter = Q(agg_filter)
        # If we build a filter for this facet, we need to add it to the
        # aggregation.
        if facet_filter:
            # If we find a `facet_field` on which apply this aggregation,
            # add a nested aggs_facet in the facet aggs (OK search)
            if facet_field:
                facet_body = dict(aggs=dict(aggs_facet=facet_body))
            facet_body['filter'] = facet_filter.to_dict()

        aggs[facet_name] = facet_body

    search = _aggregations(search, aggs)
    # Query filter
    search, urlkwargs = _query_filter(
        search, urlkwargs, facets.get('filters', {}))
    # Post filter
    search, urlkwargs = _post_filter(
        search, urlkwargs, facets.get('post_filters', {}))
    return search, urlkwargs


def _create_filter_dsl(urlkwargs, definitions):
    """Create a filter DSL expression.

    Adapt the same function defined in invenio-records-rest
    in file facets.py to the case of a dict of filters (group of
    filters).

    :param urlkwargs: MultiDict of the url parameters (facet_field,
    facet_value)
    :param definitions: the filters dictionary
    :returns: DSL expression of the filters dictionary
    """
    # simple filters
    filters = []
    # group of filters
    filters_group = {}
    for name, filter_factory in definitions.items():
        # create a filter DSL expression for a group of filters
        if isinstance(filter_factory, dict):
            filters_group[name] = []
            for f_name, f_filter_factory in filter_factory.items():
                # the url parameters values for the facet f_name of the group
                values = request.values.getlist(f_name, type=text_type)
                if values:
                    # pass the values to f_filter_factory to obtain the
                    # DSL expression and append it to filters_group
                    filters_group[name].append(f_filter_factory(values))
                    for v in values:
                        if v not in urlkwargs.getlist(f_name):
                            urlkwargs.add(f_name, v)
        # create a filter DSL expression for single filters
        else:
            # the url parameters values for the single facet name
            values = request.values.getlist(name, type=text_type)
            if values:
                # pass the values to the filter_factory to obtain the
                # DSL expression and append it to filters
                filters.append(filter_factory(values))
                for v in values:
                    if v not in urlkwargs.getlist(name):
                        urlkwargs.add(name, v)

    return filters, filters_group, urlkwargs


def _post_filter(search, urlkwargs, definitions):
    """Ingest post filter in query.

    Adapt the same function defined in invenio-records-rest
    in file facets.py to the case of a dict of filters.

    :param search: the DocumentsSearch object
    :param urlkwargs:MultiDict of the url paramenters (facet_field,
    facet_value)
    :param definitions: the filters dictionary
    :returns:
    """
    filters, filters_group, urlkwargs = \
        _create_filter_dsl(urlkwargs, definitions)

    for filter_ in filters:
        search = search.post_filter(filter_)

    for _, filter_ in filters_group.items():
        q = Q('bool', should=filter_)
        search = search.post_filter(q)

    return search, urlkwargs


def _facet_filter(index, filters, filters_group, facet_name, facet_field):
    """Ingest filter in facet.

    To take into account the selection made for other facets,
    dynamically create a filter to inject into the facet.
    This is necessary for the OR filters which are defined in the post_filters
    of the config.py file.

    :param index: the resource (ex: documents)
    :param filters: the DSL expression of the single filters defined
        in post_filters (in file config.py)
    :param filters_group: the DSL expression of a dict of filters defined
        in post_filters (in file config.py)
    :param facet_name: the facet name
    :param facet_field: the facet field
    :returns: the filter to inject in the facet
    """
    q = Q()
    for _filter in filters:
        for _, value in _filter.to_dict().items():
            filter_field = list(value.keys())[0]
            if filter_field != facet_field and _filter:
                q &= _filter

    for name_group, filters in filters_group.items():
        if facet_name != name_group and filters:
            q &= Q('bool', should=filters)
    return q if q != Q() else None
