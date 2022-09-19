# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
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
from invenio_i18n.ext import current_i18n
from invenio_records_rest.facets import _aggregations, _query_filter
from invenio_records_rest.utils import make_comma_list_a_list
from six import text_type
from werkzeug.datastructures import MultiDict


def i18n_facets_factory(search, index):
    """Add a i18n facets to search query.

    It's possible to select facets which should be added to query
    by passing their name in `facets` parameter.

    :param search: Basic search object.
    :param index: Index name.
    :returns: the new search object.
    """
    facets_config = current_app.config['RECORDS_REST_FACETS'].get(index, {})
    # i18n Aggregations.
    selected_facets = make_comma_list_a_list(
        request.args.getlist('facets', None)
    )
    all_aggs = facets_config.get("i18n_aggs", {})
    if selected_facets == []:
        selected_facets = all_aggs.keys()
    for name, agg in all_aggs.items():
        if name in selected_facets:
            i18n_agg = agg.get(
                request.args.get("lang", current_i18n.language),
                agg.get(current_app.config.get('BABEL_DEFAULT_LANGUAGE'))
            )
            search.aggs[name] = i18n_agg if not callable(i18n_agg) \
                else i18n_agg()

    return search


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

    facets = current_app.config['RECORDS_REST_FACETS'].get(index)

    if facets is not None:
        # Aggregations.
        # First get requested facets, also split by ',' to get facets names
        # if they were provided as list separated by comma.
        selected_facets = make_comma_list_a_list(
            request.args.getlist('facets', None)
        )

        all_aggs = facets.get("aggs", {})

        # Add 'author' to all_aggs
        i18n_aggs = facets.get("i18n_aggs", {})
        for facet_name, facet_body in i18n_aggs.items():
            i18n_agg = facet_body.get(
                request.args.get("lang", current_i18n.language),
                facet_body.get(current_app.config.
                               get('BABEL_DEFAULT_LANGUAGE'))
            )
            all_aggs[facet_name] = i18n_agg

        aggs = {}
        # Go through all available facets and check if they were requested.
        for facet_name, facet_body in all_aggs.items():
            # be sure that the config still untouched
            facet_body = deepcopy(facet_body)
            if not selected_facets or facet_name in selected_facets:
                # create facet_filter from post_filters
                # and inject the facet_filter into the
                # aggregation facet query
                facet_field = None
                for key in ['terms', 'date_histogram']:
                    if key in facet_body:
                        facet_field = facet_body.get(key)['field']
                        break
                if facet_field:
                    # get DSL expression of post_filters,
                    # both single post filters and group of post filters
                    filters, filters_group, urlkwargs = \
                        _create_filter_dsl(urlkwargs,
                                           facets.get('post_filters', {}))

                    # create the filter to inject in the facet
                    facet_filter = _facet_filter(
                                    index, filters, filters_group,
                                    facet_name, facet_field)
                    if 'filter' in facet_body:
                        facet_filter_cfg = Q(facet_body.pop('filter'))
                        if facet_filter:
                            facet_filter &= facet_filter_cfg
                        else:
                            facet_filter = facet_filter_cfg
                    # add a nested aggs_facet in the facet aggs
                    # and add the facet_filter to the aggregation
                    if facet_filter:
                        facet_body = dict(aggs=dict(aggs_facet=facet_body))
                        facet_body['filter'] = facet_filter.to_dict()

                aggs.update({facet_name: facet_body})
        search = _aggregations(search, aggs)

        # Query filter
        search, urlkwargs = _query_filter(
            search, urlkwargs, facets.get("filters", {}))

        # Post filter
        search, urlkwargs = _post_filter(
            search, urlkwargs, facets.get("post_filters", {}))

    return (search, urlkwargs)


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

    return (search, urlkwargs)


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
    :param face_name: the facet name
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
