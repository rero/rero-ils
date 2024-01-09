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

"""Query factories for REST API."""

from __future__ import absolute_import, print_function

import re
from datetime import datetime, timezone

from dateutil.relativedelta import relativedelta
from elasticsearch_dsl.query import Q
from flask import current_app, request
from invenio_i18n.ext import current_i18n
from invenio_records_rest.errors import InvalidQueryRESTError
from werkzeug.datastructures import ImmutableMultiDict, MultiDict

from .facets import default_facets_factory
from .modules.items.models import TypeOfItem
from .modules.organisations.api import Organisation
from .modules.patrons.api import current_librarian, current_patrons
from .modules.templates.models import TemplateVisibility
from .utils import get_i18n_supported_languages

_PUNCTUATION_REGEX = re.compile(r'[:,\?,\,,\.,;,!,=,-]+(\s+|$)')


def and_term_filter(field, **kwargs):
    """Create a term filter.

    :param field: Field name.
    :param kwargs: additional sub-filters to apply on (allowed keys are 'must'
        or 'must_not')
    :return: Function that returns a boolean AND query between term values.
    """
    def inner(values):
        _filter = Q(
            'bool',
            must=[Q('term', **{field: value}) for value in values]
        )
        for value in kwargs.get('must', []):
            _filter &= Q(**value)
        for value in kwargs.get('must_not', []):
            _filter &= ~Q(**value)
        return _filter
    return inner


def and_i18n_term_filter(field, **kwargs):
    """Create an i18n term filter.

    :param field: Field name.
    :param kwargs: additional sub-filters to apply on (allowed keys are 'must'
        or 'must_not')
    :return: Function that returns a boolean AND query between term values.
    """
    def inner(values):
        language = request.args.get('lang', current_i18n.language)
        if not language or language not in get_i18n_supported_languages():
            language = current_app.config.get('BABEL_DEFAULT_LANGUAGE', 'en')
        i18n_field = f'{field}_{language}'
        must = [Q('term', **{i18n_field: value}) for value in values]
        _filter = Q('bool', must=must)

        for value in kwargs.get('must', []):
            _filter &= Q(**value)
        for value in kwargs.get('must_not', []):
            _filter &= ~Q(**value)
        return _filter
    return inner


def i18n_terms_filter(field):
    """Create a term filter.

    :param field: Field name.
    :returns: Function that returns the Terms query.
    """
    def inner(values):
        language = request.args.get('lang', current_i18n.language)
        if not language or language not in get_i18n_supported_languages():
            language = current_app.config.get('BABEL_DEFAULT_LANGUAGE', 'en')
        i18n_field = f'{field}_{language}'
        return Q('terms', **{i18n_field: values})
    return inner


def exclude_terms_filter(field):
    """Exclude a term filter.

    :param field: Field name.
    :returns: Function that returns the Terms query.
    """
    def inner(values):
        return ~Q('terms', **{field: values})
    return inner


def or_terms_filter_by_criteria(criteria):
    """Create filter for documents based on specific criteria.

    :param criteria: filter criteria.
    :return: Function that returns a boolean OR query between term values.
    """
    def inner(values):
        should = []
        if values and values[0] == 'true':
            should.extend(
                Q('terms', **{key: criteria[key]})
                for key in criteria
            )
        return Q('bool', should=should)
    return inner


def documents_search_factory(self, search, query_parser=None):
    """Search factory with view code parameter."""
    view = request.args.get('view')
    facets = request.args.get('facets', [])
    if facets:
        facets = facets.split(',')
    # force to have organisation facet if library is set
    if 'library' in facets and 'organisation' not in facets:
        args = MultiDict(request.args)
        args.add('facets', 'organisation')
        request.args = ImmutableMultiDict(args)
    search, urlkwargs = search_factory(self, search)
    if view:
        # organisation public view
        if view != current_app.config.get('RERO_ILS_SEARCH_GLOBAL_VIEW_CODE'):
            org = Organisation.get_record_by_viewcode(view)
            search = search.filter(
                'term', holdings__organisation__organisation_pid=org['pid']
            )
        # exclude masked documents
        search = search.filter('bool', must_not=[Q('term', _masked=True)])
    # exclude draft documents
    search = search.filter('bool', must_not=[Q('term', _draft=True)])
    return search, urlkwargs


def viewcode_patron_search_factory(self, search, query_parser=None):
    """Search factory with viewcode or current patron."""
    search, urlkwargs = search_factory(self, search)
    # Public interface
    if view := request.args.get('view'):
        if view != current_app.config.get('RERO_ILS_SEARCH_GLOBAL_VIEW_CODE'):
            org = Organisation.get_record_by_viewcode(view)
            search = search.filter('term', organisation__pid=org['pid'])
    # Admin interface
    elif current_librarian:
        search = search.filter(
            'term', organisation__pid=current_librarian.organisation_pid
        )
    # exclude draft records
    search = search.filter('bool', must_not=[Q('term', _draft=True)])
    return search, urlkwargs


def holdings_search_factory(self, search, query_parser=None):
    """Search factory for holdings records."""
    search, urlkwargs = search_factory(self, search)
    view = request.args.get('view')
    search = search_factory_for_holdings_and_items(view, search)
    return search, urlkwargs


def items_search_factory(self, search, query_parser=None):
    """Search factory for item records."""
    search, urlkwargs = search_factory(self, search)
    view = request.args.get('view')
    if org_pid := request.args.get('organisation'):
        search = search.filter('term', organisation__pid=org_pid)
    search = search_factory_for_holdings_and_items(view, search)
    return search, urlkwargs


def search_factory_for_holdings_and_items(view, search):
    """Search factory for holdings and items."""
    # Logic for public interface
    if view:
        # logic for public organisational interface
        if view != current_app.config.get('RERO_ILS_SEARCH_GLOBAL_VIEW_CODE'):
            org = Organisation.get_record_by_viewcode(view)
            search = search.filter('term', organisation__pid=org['pid'])
        # masked records are hidden for all public interfaces
        search = search.filter('bool', must_not=[Q('term', _masked=True)])
        # PROVISIONAL records are hidden for all public interfaces
        search = search.filter(
            'bool', must_not=[Q('term', type=TypeOfItem.PROVISIONAL)])
    return search


def remote_entity_view_search_factory(self, search, query_parser=None):
    """Search factory with view code parameter."""
    view = request.args.get(
        'view', current_app.config.get('RERO_ILS_SEARCH_GLOBAL_VIEW_CODE'))
    search, urlkwargs = search_factory(self, search)
    if view != current_app.config.get('RERO_ILS_SEARCH_GLOBAL_VIEW_CODE'):
        org = Organisation.get_record_by_viewcode(view)
        search = search.filter('term', organisations=org['pid'])
    return search, urlkwargs


def organisation_organisation_search_factory(self, search, query_parser=None):
    """Organisation Search factory."""
    search, urlkwargs = search_factory(self, search)
    if current_librarian:
        search = search.filter('term', pid=current_librarian.organisation_pid)
    return search, urlkwargs


def organisation_search_factory(self, search, query_parser=None):
    """Search factory with view code parameter.

    Exlcude masked record from public search.
    """
    # TODO: this is a temporary implemenation of the masked holdings records.
    # this functionality will be completed after merging the USs:
    # US1909: Performance: many items on public document detailed view
    # US1906: Complete item model
    if current_librarian:
        search = search.filter(
            'term', organisation__pid=current_librarian.organisation_pid
        )
    view = request.args.get(
        'view', current_app.config.get('RERO_ILS_SEARCH_GLOBAL_VIEW_CODE'))
    search, urlkwargs = search_factory(self, search)
    if view != current_app.config.get('RERO_ILS_SEARCH_GLOBAL_VIEW_CODE'):
        search = search.filter('bool', must_not=[Q('term', _masked=True)])

    return search, urlkwargs


def view_search_collection_factory(self, search, query_parser=None):
    """Search factory with view code parameter."""
    view = request.args.get(
        'view', current_app.config.get('RERO_ILS_SEARCH_GLOBAL_VIEW_CODE'))
    search, urlkwargs = search_factory(self, search)
    if view != current_app.config.get('RERO_ILS_SEARCH_GLOBAL_VIEW_CODE'):
        org = Organisation.get_record_by_viewcode(view)
        search = search.filter(
            'term', organisation__pid=org['pid']
        )
    if published := request.args.get('published'):
        search = search.filter(
            'term', published=bool(int(published))
        )

    return search, urlkwargs


def ill_request_search_factory(self, search, query_parser=None):
    """Ill request search factory.

    Restricts results to organisation level for librarian and sys_lib.
    Restricts results to its loans for users with role patron.
    Exclude to_anonymize loans from results.
    """
    search, urlkwargs = search_factory(self, search)

    if current_librarian:
        search = search.filter(
            'term', organisation__pid=current_librarian.organisation_pid
        )
    elif current_patrons:
        search = search.filter(
            'terms',
            patron__pid=[ptrn.pid for ptrn in current_patrons])

    months = current_app.config.get('RERO_ILS_ILL_HIDE_MONTHS', 6)
    date_delta = datetime.now(timezone.utc) - relativedelta(months=months)
    filters = Q(
        'range',
        _created={'lte': 'now', 'gte': date_delta}
    )
    filters |= Q('term', status='pending')

    return search.filter(
        filters).exclude(Q('term', to_anonymize=True)), urlkwargs


def circulation_search_factory(self, search, query_parser=None):
    """Circulation search factory.

    Restricts results to organisation level for librarian and sys_lib.
    Restricts results to its loans for users with role patron.
    Exclude to_anonymize loans from results.
    """
    search, urlkwargs = search_factory(self, search)
    # a user can be patron and librarian, it should search in his own loan and
    # the loans of his profesionnal organisation

    # initial filter for OR condition
    filters = Q('match_none')
    if current_librarian:
        filters |= Q(
            'term', organisation__pid=current_librarian.organisation_pid
        )
    if current_patrons:
        filters |= Q(
            'terms',
            patron_pid=[ptrn.pid for ptrn in current_patrons]
        )
    if filters is not Q('match_none'):
        search = search.filter('bool', must=[filters])

    # exclude to_anonymize records
    search = search.filter('bool', must_not=[Q('term', to_anonymize=True)])

    return search, urlkwargs


def templates_search_factory(self, search, query_parser=None):
    """Template search factory.

    Restricts results to organisation level for librarian and sys_lib.
    Restricts results to private templates for users with role librarian.
    """
    search, urlkwargs = search_factory(self, search)
    if current_librarian:
        if current_librarian.has_full_permissions:
            search = search.filter(
                'term', organisation__pid=current_librarian.organisation_pid)
        else:
            search = search.filter(
                'term', organisation__pid=current_librarian.organisation_pid)
            search = search.filter('bool', should=[
                Q('bool', must=[
                    Q('match', creator__pid=current_librarian.pid),
                    Q('match', visibility=TemplateVisibility.PRIVATE)]),
                Q('match', visibility=TemplateVisibility.PUBLIC)])

    return search, urlkwargs


def patron_transactions_search_factory(self, search, query_parser=None):
    """Patron transaction search factory.

    Restricts results to organisation level for librarian and sys_lib.
    Restricts results to his transactions for users with role patron.
    """
    search, urlkwargs = search_factory(self, search)
    if current_librarian:
        search = search.filter(
            'term', organisation__pid=current_librarian.organisation_pid
        )
    elif current_patrons:
        search = search.filter(
            'terms',
            patron__pid=[ptrn.pid for ptrn in current_patrons])
    return search, urlkwargs


def acq_accounts_search_factory(self, search, query_parser=None):
    """Acq accounts search factory.

    Restricts results to organisation level for sys_lib.
    Restricts results to library level for librarians.
    """
    search, urlkwargs = search_factory(self, search)

    if current_librarian:
        search = search.filter(
            'term', organisation__pid=current_librarian.organisation_pid
        )
    return search, urlkwargs


def operation_logs_search_factory(self, search, query_parser=None):
    """Operation logs search factory.

    Restricts results to patron level to the current_user.
    """
    search, urlkwargs = search_factory(self, search)
    if not current_librarian and len(current_patrons):
        patron_pids = [ptrn.pid for ptrn in current_patrons]
        search = search.filter(
            'terms', loan__patron__pid=patron_pids
        )
    return search, urlkwargs


def search_factory(self, search, query_parser=None):
    """Parse query using elasticsearch DSL query.

    Terms defined by: RERO_ILS_QUERY_BOOSTING will be boosted
    at the query level.

    :param self: REST view.
    :param search: Elastic search DSL search instance.
    :param query_parser: a specific query parser
    :return: Tuple with search instance and URL arguments.
    """
    def _default_parser(qstr=None, query_boosting=None):
        """Default parser that uses the Q() from elasticsearch_dsl."""
        query_type = 'query_string'
        # avoid elasticsearch errors when it can't convert a boolean or
        # numerical values during the query
        lenient = True
        default_operator = 'OR'
        if request.args.get('simple') == '1':
            query_type = 'simple_query_string'
            default_operator = 'AND'

        if qstr:
            # TODO: remove this bad hack
            qstr = _PUNCTUATION_REGEX.sub(' ', qstr)
            qstr = re.sub(r'\s+', ' ', qstr).rstrip()
            return (
                Q(
                    query_type,
                    lenient=lenient,
                    query=qstr,
                    boost=2,
                    fields=query_boosting,
                    default_operator=default_operator,
                )
                | Q(
                    query_type,
                    lenient=lenient,
                    query=qstr,
                    default_operator=default_operator,
                )
                if query_boosting
                else Q(
                    query_type,
                    lenient=lenient,
                    query=qstr,
                    default_operator=default_operator,
                )
            )
        return Q()

    def _boosting_parser(query_boosting, search_index):
        """Elasticsearch boosting fields parser."""
        boosting = []
        if search_index in query_boosting:
            boosting.extend([
                f'{field}^{boost}'
                for field, boost in query_boosting[search_index].items()
            ])

        return boosting

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
    except SyntaxError as err:
        query = request.values.get('q', '')
        current_app.logger.debug(
            f'Failed parsing query: {query}',
            exc_info=True,
        )
        raise InvalidQueryRESTError() from err

    search, urlkwargs = default_facets_factory(search, search_index)
    search, sortkwargs = default_sorter_factory(search, search_index)
    for key, value in sortkwargs.items():
        urlkwargs.add(key, value)
    urlkwargs.add('q', query_string)
    return search, urlkwargs
