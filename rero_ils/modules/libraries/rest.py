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

"""REST API endpoint for about `Library`."""

from abc import abstractmethod

from elasticsearch_dsl import Q
from flask import jsonify, request
from invenio_records_rest.views import pass_record
from invenio_rest import ContentNegotiatedMethodView

from rero_ils.modules.decorators import check_logged_as_librarian, \
    query_string_extract_histogram_interval_param, \
    query_string_extract_interval_param, \
    query_string_extract_operations_param, \
    query_string_extract_time_range_boundary
from rero_ils.modules.libraries.statistics import get_document_type_repartition
from rero_ils.modules.loans.logs.statistics import \
    get_circulation_statistics, get_rate_circulation_statistics


class DefaultJSONResource(ContentNegotiatedMethodView):
    """Default abstract class to return JSON content."""

    def __init__(self, **kwargs):
        """Initialization method."""
        super().__init__(
            method_serializers={
                'GET': {
                    'application/json': jsonify
                }
            },
            serializers_query_aliases={
                'json': 'application/json'
            },
            default_method_media_type={
                'GET': 'application/json'
            },
            default_media_type='application/json',
            **kwargs
        )

    @abstractmethod
    def get(self, **kwargs):
        """HTTP GET method handler."""
        return NotImplemented()


class LibraryCirculationStatisticsResource(DefaultJSONResource):
    """API endpoint to get the circulation statistics about a library.

    This view return circulation operation statistics for a library.

    Statistics scope could be specified using some query string arguments :
      * `operation`: the list of circulation operations to analyze.
      * `from`: the lower interval time limit used to analyze statistics.
      * `to`: the upper interval time limit used to analyze statistics.
      * `interval`: the interval to use between each step of the stat results.
            If no interval is specified, a default interval will be chosen
            depending on the timestamp request boundary (defined by from|to
            arguments). See official ElasticSearch document for more details
            about interval syntax.

    Usage examples:
      <endpoint>?from=now-1Y&to=now-2d&interval=2M&operation=checkin
      <endpoint>?from=now-1Y&operation=checkin,checkout
      <endpoint>?from=now-1Y&operation=checkin&operation=checkout
    """

    @check_logged_as_librarian
    @pass_record
    @query_string_extract_histogram_interval_param
    @query_string_extract_operations_param
    def get(self, pid, record, operations, **kwargs):
        """HTTP GET method handler.

        :param pid: the PID identifier of the library.
        :param record: the library resource instance.
        :param operations: circulation operations list to filter.
        :param kwargs: optional parameters parsed from query string
          * from: the lower interval date limit.
          * to: the upper interval date limit.
          * interval: the interval to use between each step of the stat results
        """
        filters = [
            Q('terms', loan__transaction_location__pid=record.location_pids()),
            Q('terms', loan__trigger=operations)
        ]
        return self.make_response(
            get_circulation_statistics(filters, **kwargs)
        )


class LibraryCirculationRateStatisticsResource(DefaultJSONResource):
    """API endpoint to get the circulation rate statistics about a library.

    This view return circulation operation rate statistics for a library.
    Circulation rate is the number of operation distributed on a period of time
    (typically a full day) but analyzing data for a longer time period. So
    two operations executed at same minutes of the day but on two different
    days will be aggregate on the same result key.

    Statistics scope could be specified using some query string arguments :
      * `operation`: the list of circulation operations to analyze.
      * `from`: the lower interval time limit used to analyze statistics.
      * `to`: the upper interval time limit used to analyze statistics.
      * `interval`: the interval to use between each step of the stat results.
            If no interval is specified, a default interval will be chosen
            depending on the timestamp request boundary (defined by from|to
            arguments). See official ElasticSearch document for more details
            about interval syntax.

    Usage examples:
      <endpoint>?from=now-1Y&to=now-2d&interval=2M&operation=checkin
      <endpoint>?from=now-1Y&operation=checkin,checkout
      <endpoint>?from=now-1Y&operation=checkin&operation=checkout
    """

    @check_logged_as_librarian
    @pass_record
    @query_string_extract_operations_param
    @query_string_extract_interval_param(default_value=1)
    @query_string_extract_time_range_boundary
    def get(self, pid, record, operations, **kwargs):
        """HTTP GET method handler.

        :param pid: the PID identifier of the library.
        :param record: the library resource instance.
        :param operations: circulation operations list to filter.
        :param kwargs: optional parameters parsed from query string
          * from: the lower interval date limit.
          * to: the upper interval date limit.
          * interval: the interval to use between each step of the stat results
        """
        filters = [
            Q('terms', loan__transaction_location__pid=record.location_pids()),
            Q('terms', loan__trigger=operations)
        ]
        return self.make_response(get_rate_circulation_statistics(
            filters=filters,
            operations=operations,
            interval=kwargs.pop('interval', 1),
            **kwargs
        ))


class LibraryDocumentTypeRepartitionResource(DefaultJSONResource):
    """API endpoint to get the repartition of document type about a library.

    Statistics scope could be specified using some query string arguments :
      * docType: the main document type. If present the response output will
            be the repartition by subtype of this main document type.
      * exclude: a list a values to excludes from response. Repeat parameter to
            exclude multiple value

    Usage examples:
      <endpoint>?docType=main_type&exclude=sub_type
      <endpoint>?exclude=main_type1&exclude=main_type2
      <endpoint>?exclude=main_type1,main_type2
    """

    @check_logged_as_librarian
    @pass_record
    def get(self, pid, record, **kwargs):
        """HTTP GET method handler.

        :param pid: the PID identifier of the library.
        :param record: the library resource instance.
        """
        kwargs = {'excludes': request.args.getlist('exclude')}
        if 'docType' in request.args:
            kwargs['document_type'] = request.args['docType']
        return self.make_response(
            get_document_type_repartition(record, **kwargs)
        )
