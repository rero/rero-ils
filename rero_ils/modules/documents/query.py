# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2022 RERO
# Copyright (C) 2022 UCLouvain
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
import re

from elasticsearch_dsl import Q
from flask import request


def acquisition_filter():
    """Create a nested filter for new acquisition.

    :return: Function that returns a nested query to retrieve new acquisition
    """
    def inner(values):

        # `values` params could contains one or two values. Values must be
        # separate by a ':' character. Values are :
        #   1) from_date (optional) : the lower limit range acquisition_date.
        #        this date will be included into the search result ('<=').
        #        if not specified the '*' value will be used
        #   2) until_date (optional) : the upper limit range acquisition_date.
        #        this date will be excluded from the search result ('>').
        #        if not specified the current timestamp value will be used
        #  !!! Other filters could be used to restrict data result : This
        #      function will check for 'organisation' and/or 'library' and/or
        #      'location' url parameter to limit query result.
        #
        #   SOME EXAMPLES :
        #     * ?new_acquisition=2020-01-01&organisation=1
        #       --> all new acq for org with pid=1 from 2020-01-01 to now
        #     * ?library=3&new_acquisition=2020-01-01:2021-01-01
        #       --> all new acq for library with pid=3 for the 2020 year
        #     * ?location=17&library=2&new_acquisition=:2020-01-01
        #       --> all new acq for (location with pid=17 and library with
        #           pid=2) until Jan, 1 2020

        # build acquisition date range query
        values = dict(zip(['from', 'to'], values.pop().split(':')))
        range_acquisition_dates = {'lt': values.get('to') or 'now/d'}
        if values.get('from'):
            range_acquisition_dates['gte'] = values.get('from')

        # build general 'match' query (including acq date range query)
        must_queries = [Q(
            'range',
            holdings__items__acquisition__date=range_acquisition_dates
        )]

        # Check others filters from command line and add them to the query if
        # needed
        for level in ['location', 'library', 'organisation']:
            if arg := request.args.get(level):
                field = 'holdings__items__acquisition__{0}_pid'.format(level)
                must_queries.append(Q('match', **{field: arg}))

        return Q(
            'nested',
            path='holdings.items.acquisition',
            query=Q('bool', must=must_queries)
        )
    return inner


def nested_identified_filter():
    """Create a nested filter for document identifiers.

    :return: Function that returns a nested query to document containing
             specified identifiers
    """

    def _build_nested_identifier_query(identifier):
        # Next regexp capture identifier type and value. For example :
        #  * "123456789" --> id_value=123456789
        #  * "(bf:Isbn)123456789 --> id_type=bf:Isbn, id_value=123456789
        #  * "(bf:Local)kw(2) --> id_type=bf:Local, id_value=kw(2)
        regexp = re.compile(r'^(\((?P<id_type>[\w\d:]+)\))?(?P<id_value>.*)$')
        matches = re.match(regexp, identifier)

        # DEV NOTES : Wildcard query on text fields referencing an analyzer
        # failed since ES version 7.13.0.
        # https://github.com/elastic/elasticsearch/issues/87728
        #
        # a work-around is to use a 'query-string' query and specify the
        # analyzer to use and enable the wildcard characters analyze
        #
        # old smart criteria was:
        # >>> Q('wildcard', nested_identifiers__value=matches['id_value'])
        criteria = Q(
            'query_string',
            query=matches['id_value'],
            fields=['nested_identifiers.value'],
            analyzer="identifier-analyzer",
            analyze_wildcard=True
        )

        if matches['id_type']:
            criteria &= Q('match', nested_identifiers__type=matches['id_type'])
        return Q('nested', path='nested_identifiers', query=criteria)

    def inner(identifiers):
        queries = [
            _build_nested_identifier_query(identifier)
            for identifier in identifiers
        ]
        return Q('bool', should=queries)

    return inner
