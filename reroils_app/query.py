# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
# Copyright (C) 2016-2018 RERO.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Query factories for REST API."""

from __future__ import absolute_import, print_function

from elasticsearch_dsl.query import Q
from flask import current_app, request
from invenio_records_rest.errors import InvalidQueryRESTError


def and_search_factory(self, search, query_parser=None):
    """Parse query using elasticsearch DSL query.

    :param self: REST view.
    :param search: Elastic search DSL search instance.
    :returns: Tuple with search instance and URL arguments.
    """
    def _default_parser(qstr=None):
        """Default parser that uses the Q() from elasticsearch_dsl."""
        if qstr:
            return Q('query_string', query=qstr, default_operator='AND')
        return Q()

    from invenio_records_rest.facets import default_facets_factory
    from invenio_records_rest.sorter import default_sorter_factory

    query_string = request.values.get('q')
    query_parser = query_parser or _default_parser

    try:
        search = search.query(query_parser(query_string))
    except SyntaxError:
        current_app.logger.debug(
            "Failed parsing query: {0}".format(
                request.values.get('q', '')),
            exc_info=True)
        raise InvalidQueryRESTError()

    search_index = search._index[0]
    search, urlkwargs = default_facets_factory(search, search_index)
    search, sortkwargs = default_sorter_factory(search, search_index)
    for key, value in sortkwargs.items():
        urlkwargs.add(key, value)

    urlkwargs.add('q', query_string)
    return search, urlkwargs
