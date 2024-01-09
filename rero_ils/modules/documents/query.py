# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
# Copyright (C) 2019-2023 UCLouvain
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
from datetime import datetime

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
        #        this date will be included from the search result ('>=').
        #        if not specified the current timestamp value will be used
        #  !!! Other filters could be used to restrict data result : This
        #      function will check for 'organisation' and/or 'library' and/or
        #      'location' url parameter to limit query result.
        #
        #   SOME EXAMPLES :
        #     * ?new_acquisition=2020-01-01&organisation=1
        #       --> all new acq for org with pid=1 from 2020-01-01 to now
        #     * ?library=3&new_acquisition=2020-01-01:2020-12-31
        #       --> all new acq for library with pid=3 for the 2020 year
        #     * ?location=17&library=2&new_acquisition=:2019-12-31
        #       --> all new acq for (location with pid=17 and library with
        #           pid=2) until Jan, 1 2020

        # build acquisition date range query
        range_values = values.pop()
        if '--' in range_values:
            # NG-Core's widget for a date range sends timestamps
            # We transform the timestamp into a date
            values = dict(zip(['from', 'to'], range_values.split('--')))
            if 'from' in values:
                values['from'] = datetime.fromtimestamp(
                    float(values['from'])/1000).strftime('%Y-%m-%d')
            if 'to' in values:
                values['to'] = datetime.fromtimestamp(
                    float(values['to'])/1000).strftime('%Y-%m-%d')
        else:
            values = dict(zip(['from', 'to'], range_values.split(':')))
        range_acquisition_dates = {'lte': values.get('to') or 'now/d'}
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
                field = f'holdings__items__acquisition__{level}_pid'
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
        criteria = Q('wildcard', nested_identifiers__value=matches['id_value'])
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
