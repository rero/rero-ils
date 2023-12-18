# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
# Copyright (C) 2019-2022 UCLouvain
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

from flask import Blueprint, current_app, jsonify
from flask import request as flask_request
from invenio_records_rest.utils import obj_or_import_string
from invenio_rest import ContentNegotiatedMethodView

from rero_ils.modules.decorators import check_logged_as_librarian

from .exceptions import ResultNotFoundOnTheRemoteServer
from .serializers import json_record_serializer_factory, \
    json_v1_import_record_marc, json_v1_import_search, \
    json_v1_import_uisearch

api_blueprint = Blueprint(
    'api_import',
    __name__,
    url_prefix='/imports'
)


@api_blueprint.route('/config/', methods=['GET'])
@check_logged_as_librarian
def get_config():
    """Get configuration from config.py."""
    sources = current_app.config.get('RERO_IMPORT_REST_ENDPOINTS', {}).values()
    for source in sources:
        source.pop('import_class', None)
        source.pop('import_size', None)
    return jsonify(sorted(sources, key=lambda s: s.get('weight', 100)))


class ImportsListResource(ContentNegotiatedMethodView):
    """Imports REST resource."""

    def __init__(self, **kwargs):
        """Init."""
        self.import_class = obj_or_import_string(kwargs.pop('import_class'))
        self.import_size = kwargs.pop('import_size', 50)
        super().__init__(
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
        """Implement the GET."""
        no_cache = True if flask_request.args.get('no_cache') else False
        query = flask_request.args.get('q')
        try:
            query_split = query.split(':')
            where = query_split[0]
            relation = query_split[1]
            what = ':'.join(query_split[2:])
        except Exception:
            where = 'anywhere'
            relation = 'all'
            what = query
        size = flask_request.args.get('size', self.import_size)
        do_import = self.import_class()
        results, status_code = do_import.search_records(
            what=what,
            relation=relation,
            where=where,
            max_results=size,
            no_cache=no_cache
        )
        filter_year = flask_request.args.get('year')
        if filter_year:
            ids = do_import.get_ids_for_aggregation(
                results=results,
                aggregation='year',
                key=int(filter_year)
            )
            results = do_import.filter_records(results, ids)
        filter_type = flask_request.args.get('document_type')
        if filter_type:
            sub_filter_type = flask_request.args.get('document_subtype')
            if sub_filter_type:
                ids = do_import.get_ids_for_aggregation_sub(
                    results=results,
                    agg='document_type',
                    key=filter_type,
                    sub_agg='document_subtype',
                    sub_key=sub_filter_type
                )
            else:
                ids = do_import.get_ids_for_aggregation(
                    results=results,
                    aggregation='document_type',
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
        filter_language = flask_request.args.get('language')
        if filter_language:
            ids = do_import.get_ids_for_aggregation(
                results=results,
                aggregation='language',
                key=filter_language
            )
            results = do_import.filter_records(results, ids)
        # return None, results
        response = self.make_response(pid_fetcher=None, search_result=results)
        response.status_code = status_code
        return response


class ImportsResource(ContentNegotiatedMethodView):
    """Imports REST resource."""

    def __init__(self, **kwargs):
        """Init."""
        self.import_class = obj_or_import_string(kwargs.pop('import_class'))
        self.import_size = kwargs.pop('import_size', 50)
        super().__init__(
            method_serializers={
                'GET': {
                    'application/json': json_record_serializer_factory(
                        self.import_class
                    ),
                    'application/rero+json': json_record_serializer_factory(
                        self.import_class, serializer_type='uirecord'
                    ),
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
        no_cache = True if flask_request.args.get('no_cache') else False
        size = flask_request.args.get('size', self.import_size)
        do_import = self.import_class()
        do_import.search_records(
            what=id,
            relation='all',
            where='recordid',
            max_results=size,
            no_cache=no_cache
        )
        if not do_import.data:
            raise ResultNotFoundOnTheRemoteServer
        return 0, do_import.data[0]
