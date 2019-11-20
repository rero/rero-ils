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
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Query factories for REST API."""

from __future__ import absolute_import, print_function

from elasticsearch_dsl import A
from elasticsearch_dsl.query import Q
from flask import current_app, request
from invenio_records_rest.errors import InvalidQueryRESTError

from .modules.organisations.api import Organisation
from .modules.patrons.api import current_patron


def document_search_factory(self, search, query_parser=None):
    """Document search factory.

    Dynamic addition of an organisation or library facet
    depending on the view parameter (global or locale).
    """
    agg_size = current_app.config.get('RERO_ILS_AGGREGATION_SIZE').get(
        'documents', current_app.config.get(
            'RERO_ILS_DEFAULT_AGGREGATION_SIZE'))
    view = request.args.get(
        'view', current_app.config.get('RERO_ILS_SEARCH_GLOBAL_VIEW_CODE'))
    if view == current_app.config.get('RERO_ILS_SEARCH_GLOBAL_VIEW_CODE'):
        agg = A(
            'terms',
            field='holdings.organisation.organisation_pid',
            size=agg_size)
        search.aggs.bucket('organisation', agg)
    else:
        org_pid = Organisation.get_record_by_viewcode(view)['pid']
        agg = A(
            'terms',
            field='holdings.organisation.organisation_library',
            include='{}\\-[0-9]*'.format(org_pid),
            size=agg_size
        )
        search.aggs.bucket('library', agg)
    return view_search_factory(self, search, query_parser)


def view_search_factory(self, search, query_parser=None):
    """Search factory with view code parameter."""
    view = request.args.get(
        'view', current_app.config.get('RERO_ILS_SEARCH_GLOBAL_VIEW_CODE'))
    search, urlkwargs = search_factory(self, search)
    if view != current_app.config.get('RERO_ILS_SEARCH_GLOBAL_VIEW_CODE'):
        org = Organisation.get_record_by_viewcode(view)
        search = search.filter(
            'term', **{'holdings__organisation__organisation_pid': org['pid']}
        )
    return (search, urlkwargs)


def organisation_search_factory(self, search, query_parser=None):
    """Search factory."""
    search, urlkwargs = search_factory(self, search)
    if current_patron:
        search = search.filter(
            'term', organisation__pid=current_patron.get_organisation()['pid'])
    return (search, urlkwargs)


def loans_search_factory(self, search, query_parser=None):
    """Loan search factory.

    Restricts results to oraganisation level for librarian and sys_lib.
    Restricts results to his loans for users with role patron.
    """
    search, urlkwargs = search_factory(self, search)
    if current_patron:
        if current_patron.is_librarian or current_patron.is_system_librarian:
            search = search.filter(
                'term', organisation__pid=current_patron.get_organisation(
                    )['pid'])
        if current_patron.is_patron:
            search = search.filter(
                'term', patron_pid=current_patron.pid)
    return (search, urlkwargs)


def search_factory(self, search, query_parser=None):
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
                return Q('query_string', query=qstr)
            else:
                return Q('bool', should=[
                    Q('query_string', query=qstr, boost=2,
                        fields=query_boosting),
                    Q('query_string', query=qstr)
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
    display_score = request.values.get('display_score')
    if display_score:
        search = search.extra(explain=True)
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
