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

"""Methods used to get statistics about `LoanOperationLog`."""
from copy import deepcopy

from elasticsearch_dsl import A, Q
from flask import current_app as app
from invenio_search import RecordsSearch

from rero_ils.modules.loans.logs.api import LoanOperationLog


def _build_date_filters(_from, _to, default_values=None):
    """Build parameters for date range filter to apply on ElasticSearch query.

    :param _from: (string) the date range lower limit.
    :param _to: (string) the date range upper limit.
    :param default_values: (string, string) a tuple with default values if
       `_from`, '_to` isn't specified.
    :returns: a dictionary of params to apply on ElasticSearch range filter.
    """
    default_values = default_values or ('now-7d', 'now')
    assert len(default_values) == 2, '2 default values are required'
    date_range = {
        'gte': _from or default_values[0],
        'lte': _to or default_values[1]
    }
    return {k: v for k, v in date_range.items() if v != '*'}


def get_circulation_statistics(filters=None, interval=None, **kwargs):
    """Get the statistics about circulation operations.

    :param filters: a list of criteria to apply to filter the operation
        logs index.
    :param interval: a tuple representing the interval for each step of
        statistics. Each tuple must provide 2 values :
          * the interval type : 'calendar_interval' or 'fixed_interval'
          * the interval value to use corresponding to the type.
        See official ElasticSearch document for more explanations.
    :param kwargs: any additional named parameters. Useful key are:
        * `from` : the transaction lower boundary interval limit (included)
        * `to`: the transaction upper boundary interval limit (include)
    """
    # define default parameters if not specified
    filters = filters or []
    filters.append(Q('term', record__type='loan'))
    if date_range := _build_date_filters(kwargs.get('from'), kwargs.get('to')):
        filters.append(Q('range', date=date_range))

    # build date histogram aggregations
    interval = interval or ('calendar_interval', '1d')
    params = {
        interval[0]: interval[1],  # interval_type: interval_value
        'format': kwargs.get('format', 'yyyy-MM-dd')
    }
    agg = A('date_histogram', field='date', **params)
    agg.bucket('operation', A('terms', field='loan.trigger'))

    # Build the search and execute it.
    # Create the stat result data based on search result.
    query = RecordsSearch(index=LoanOperationLog.index_name)[:0] \
        .query('bool', filter=filters)
    query.aggs.bucket('operations', agg)
    results = query.execute()

    return {
        time_interval.key_as_string: {
            'total': time_interval.doc_count,
            'operations': {
                operation.key: operation.doc_count
                for operation in time_interval.operation.buckets
            }
        }
        for time_interval in results.aggregations.operations.buckets
    }


def get_rate_circulation_statistics(
    filters=None, interval=1, operations=None, **kwargs
):
    """Get rate statistics (HH:mm) about circulation operations.

    Get circulation statistics filtered with some filters and get the
    aggregates them by minutes of the day.

    :param filters: a list of criteria to apply to filter the operation
        logs index.
    :param interval: the number of minutes between each result step.
    :param operations: the list of operation name to analyze.
    :param kwargs: any additional named parameters. Useful key are:
        * `from` : the transaction lower boundary interval limit (included)
        * `to`: the transaction upper boundary interval limit (include)
    :return: a dictionary representing circulation operation by minutes of
        the day. Each entry key representing the minutes of the day using
        format `HH:mm`, each entry values is a dictionary where circulation
        operation/counter are describe.

    >> {
    >>    '00:01': {'checkin': 0, 'checkout':3, 'renewal':0 },
    >>    '00:02': {'checkin': 2, 'checkout':5, 'renewal':3 },
    >>    ...
    >> }
    """
    # 1) Build filters to use to filter the search result
    # 2) Add histogram aggregation to the query
    # 3) Execute the query
    filters = filters or []
    filters.append(Q('term', record__type='loan'))
    if date_range := _build_date_filters(kwargs.get('from'), kwargs.get('to')):
        filters.append(Q('range', date=date_range))
    agg = A(
        'histogram',
        script='doc["date"].value.get(ChronoField.MINUTE_OF_DAY)',
        min_doc_count=1,
        interval=interval
    )
    agg.bucket('operation', A('terms', field='loan.trigger'))
    search = RecordsSearch(index=LoanOperationLog.index_name) \
        .query('bool', filter=filters)
    search.aggs.bucket('operations', agg)
    search = search[:0]
    results = search.execute()

    # Build the default statistic results
    operations = operations or app.config.get('CIRCULATION_BASIC_OPERATIONS')
    operations_data = {operation: 0 for operation in operations}
    stats = {
        f'{idx // 60:02d}:{idx % 60:02d}': deepcopy(operations_data)
        for idx in range(0, 1440, interval)
    }

    # Analyze the ES query response to populate the stats dictionary
    for aggr in results.aggregations.operations.buckets:
        minute_of_day = int(aggr.key)
        key = f'{minute_of_day // 60:02d}:{minute_of_day % 60:02d}'
        for operation in aggr.operation:
            if operation.key in operations:
                stats[key][operation.key] += operation.doc_count
    return stats
