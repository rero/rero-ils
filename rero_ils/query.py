# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Query factories for REST API."""

from __future__ import absolute_import, print_function

from elasticsearch_dsl.query import Q
from flask import current_app, request
from invenio_records_rest.errors import InvalidQueryRESTError
from invenio_records_rest.sorter import eval_field

from .modules.patrons.api import current_patron


def organisation_search_factory(self, search, query_parser=None):
    """Search factory."""
    search, urlkwargs = and_search_factory(self, search)
    if current_patron:
        search = search.filter(
            'term', organisation__pid=current_patron.get_organisation()['pid'])
    return (search, urlkwargs)


def and_search_factory(self, search, query_parser=None):
    """Parse query using elasticsearch DSL query.

    Terms defined by: RERO_ILS_QUERY_BOOSTING will be boosted
    at the query level.

    :param self: REST view.
    :param search: Elastic search DSL search instance.
    :returns: Tuple with search instance and URL arguments.
    """
    def _default_parser(qstr=None, query_boosting=[]):
        """Default parser that uses the Q() from elasticsearch_dsl."""
        if qstr:
            if not query_boosting:
                return Q('query_string', query=qstr, default_operator='AND')
            else:
                return Q('bool', should=[
                    Q('query_string', query=qstr, boost=2,
                        fields=query_boosting, default_operator="AND"),
                    Q('query_string', query=qstr, default_operator="AND")
                ])
        return Q()

    def _boosting_parser(query_boosting, search_index):
        """Elasticsearch boosting fields parser."""
        boosting = []
        if search_index in query_boosting:
            for field, boost in query_boosting[search_index].items():
                boosting.append('{}^{}'.format(field, boost))
        return boosting

    from invenio_records_rest.facets import default_facets_factory
    from invenio_records_rest.sorter import default_sorter_factory

    query_string = request.values.get('q')
    query_parser = query_parser or _default_parser

    search_index = search._index[0]
    query_boosting = _boosting_parser(
        current_app.config['RERO_ILS_QUERY_BOOSTING'],
        search_index
    )

    try:
        search = search.query(query_parser(query_string, query_boosting))
    except SyntaxError:
        current_app.logger.debug(
            'Failed parsing query: {0}'.format(request.values.get('q', '')),
            exc_info=True,
        )
        raise InvalidQueryRESTError()

    search, urlkwargs = default_facets_factory(search, search_index)
    search, sortkwargs = default_sorter_factory(search, search_index)
    for key, value in sortkwargs.items():
        urlkwargs.add(key, value)

    urlkwargs.add('q', query_string)
    return search, urlkwargs
