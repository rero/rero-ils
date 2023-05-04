# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
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

from flask import current_app
from flask import request as flask_request
from invenio_rest import ContentNegotiatedMethodView
from werkzeug.exceptions import HTTPException
from werkzeug.wrappers import Response

from .cql_parser import Diagnostic, parse
from .explaine import Explain
from ..documents.api import DocumentsSearch, document_id_fetcher
from ..documents.serializers import json_doc_search, xml_dc_search, \
    xml_marcxmlsru_search
from ..utils import strip_chars


class SRUDocumentsSearch(ContentNegotiatedMethodView):
    """SRU search REST resource."""

    # TODO: is candidate for invenio-record-resource ?

    def __init__(self, **kwargs):
        """Init."""
        super().__init__(
            method_serializers={
                'GET': {
                    'application/xml': xml_marcxmlsru_search,
                    'application/xml+dc': xml_dc_search,
                    'application/rero+json': json_doc_search,
                }
            },
            serializers_query_aliases={
                'marcxmlsru': 'application/xml',
                'dc': 'application/xml+dc',
                'json': 'application/rero+json'
            },
            default_method_media_type={
                'GET': 'application/xml'
            },
            default_media_type='application/xml',
            **kwargs
        )

    def get(self, **kwargs):
        """Implement the GET /sru/documents."""
        operation = flask_request.args.get('operation', None)
        query = flask_request.args.get('query', None)
        version = flask_request.args.get('version', '1.1')
        start_record = max(int(flask_request.args.get('startRecord', 1)), 1)
        maximum_records = min(
            int(flask_request.args.get(
                'maximumRecords',
                current_app.config.get('RERO_SRU_NUMBER_OF_RECORDS', 100)
            )),
            current_app.config.get('RERO_SRU_MAXIMUM_RECORDS', 1000)
        )
        # TODO: enable es query string
        # query_string = flask_request.args.get('q', None)
        if operation == 'searchRetrieve' and query:  # or query_string:
            try:
                query_string = parse(query).to_es()
            except Diagnostic as err:
                response = Response(err.xml_str())
                response.headers['content-type'] = 'application/xml'
                raise HTTPException(response=response)

            search = DocumentsSearch().query(
                'query_string', query=query_string)
            records = []
            search = search[(start_record-1):maximum_records+(start_record-1)]
            for hit in search.execute():
                records.append({
                    '_id': hit.meta.id,
                    '_index': hit.meta.index,
                    '_source': hit.to_dict(),
                    '_version': 0
                })

            result = {
                'hits': {
                    'hits': records,
                    'total': {
                        'value': search.count(),
                        'relation': 'eq'
                    },
                    'sru': {
                        'query': strip_chars(query),
                        'query_es': query_string,
                        'start_record': start_record,
                        'maximum_records': maximum_records
                    }
                }
            }
            return self.make_response(
                pid_fetcher=document_id_fetcher,
                search_result=result
            )

        explain = Explain('api/sru/documents')
        response = Response(str(explain))
        response.headers['content-type'] = 'application/xml'
        raise HTTPException(response=response)
