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

"""Blueprint used for loading templates."""

from __future__ import absolute_import, print_function

from flask import request as flask_request
from invenio_records_rest.utils import obj_or_import_string
from invenio_rest import ContentNegotiatedMethodView
from invenio_rest.errors import RESTException

from .serializers import json_v1_import_record, json_v1_import_record_marc, \
    json_v1_import_search, json_v1_import_uirecord, json_v1_import_uisearch


class ResultNotFoundOnTheRemoteServer(RESTException):
    """Non existant remote record."""

    code = 404
    description = 'Record not found on the remote server.'


class ImportsListResource(ContentNegotiatedMethodView):
    """Imports REST resource."""

    def __init__(self, **kwargs):
        """Init."""
        self.import_class = kwargs.pop('import_class')
        self.import_size = kwargs.pop('import_size', 50)
        super(ImportsListResource, self).__init__(
            method_serializers={
                'GET': {
                    'application/json': json_v1_import_search,
                    'application/rero+json': json_v1_import_uisearch
                }
            },
            serializers_query_aliases={
                'json': 'application/json',
                'rerojson': 'application/rero+json'
            },
            default_method_media_type={
                'GET': 'application/json'
            },
            default_media_type='application/json',
            **kwargs
        )

    def get(self, **kwargs):
        """Implement the GET /test."""
        no_cache = True if flask_request.args.get('no_cache') else False
        query = flask_request.args.get('q')
        try:
            query_split = query.split(':')
            where = query_split[0]
            relation = query_split[1]
            what = ':'.join(query_split[2:])
        except:
            where = 'anywhere'
            relation = 'all'
            what = query
        size = flask_request.args.get('size', self.import_size)
        do_import = obj_or_import_string(self.import_class)()
        do_import.search_records(what=what, relation=relation,
                                 where=where, max=size, no_cache=no_cache)
        results = do_import.results
        filter_year = flask_request.args.get('year')
        if filter_year:
            ids = do_import.get_ids_for_aggregation(
                results=results,
                aggregation='year',
                key=int(filter_year)
            )
            results = do_import.filter_records(results, ids)
        filter_type = flask_request.args.get('type')
        if filter_type:
            ids = do_import.get_ids_for_aggregation(
                results=results,
                aggregation='type',
                key=filter_type
            )
            results = do_import.filter_records(results, ids)
        filter_author = flask_request.args.get('author')
        if filter_author:
            ids = do_import.get_ids_for_aggregation(
                results=results,
                aggregation='author',
                key=filter_author
            )
            results = do_import.filter_records(results, ids)
        return None, results


class ImportsResource(ContentNegotiatedMethodView):
    """Imports REST resource."""

    def __init__(self, **kwargs):
        """Init."""
        self.import_class = kwargs.pop('import_class')
        super(ImportsResource, self).__init__(
            method_serializers={
                'GET': {
                    'application/json': json_v1_import_record,
                    'application/rero+json': json_v1_import_uirecord,
                    'application/marc+json': json_v1_import_record_marc
                }
            },
            serializers_query_aliases={
                'json': 'application/json',
                'rerojson': 'application/rero+json',
                'marc': 'application/marc+json'
            },
            default_method_media_type={
                'GET': 'application/json'
            },
            default_media_type='application/json',
            **kwargs
        )

    def get(self, id, **kwargs):
        """Implement the GET."""
        do_import = obj_or_import_string(self.import_class)()
        do_import.search_records(
            what=id,
            relation='all',
            where='recordid',
            max=1
        )
        if not do_import.data:
            raise ResultNotFoundOnTheRemoteServer
        return 0, do_import.data[0]
