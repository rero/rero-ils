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

"""Record serialization."""
from flask import json, request, url_for
from invenio_records_rest.schemas import \
    RecordSchemaJSONV1 as _RecordSchemaJSONV1
from invenio_records_rest.serializers.json import \
    JSONSerializer as _JSONSerializer
from invenio_records_rest.serializers.response import record_responsify, \
    search_responsify
from marshmallow import fields


class RecordSchemaJSONV1(_RecordSchemaJSONV1):
    """Schema for records RERO ILS in JSON.

    Add a permissions field.
    """

    permissions = fields.Raw()
    explanation = fields.Raw()


class JSONSerializer(_JSONSerializer):
    """Mixin serializing records as JSON."""

    def preprocess_record(self, pid, record, links_factory=None, **kwargs):
        """Prepare a record and persistent identifier for serialization."""
        rec = record
        if request and request.args.get('resolve') == '1':
            rec = record.replace_refs()
            # because the replace_refs loose the record original model. We need
            # to resetting it to have correct 'created'/'updated' output data
            rec.model = record.model
        return super().preprocess_record(
            pid=pid, record=rec, links_factory=links_factory, kwargs=kwargs)

    @staticmethod
    def preprocess_search_hit(pid, record_hit, links_factory=None, **kwargs):
        """Prepare a record hit from Elasticsearch for serialization."""
        record = _JSONSerializer.preprocess_search_hit(
            pid=pid,
            record_hit=record_hit,
            links_factory=links_factory,
            kwargs=kwargs
        )
        if record.get('_explanation'):
            record[1:] = record.get('_explanation')
            del record['_explanation']
        return record

    def post_process_serialize_search(self, results, pid_fetcher):
        """Post process the search results."""
        pid_type = pid_fetcher(None, dict(pid='1')).pid_type
        results['links'].update({
            'create': url_for('invenio_records_rest.{pid_type}_list'.format(
                        pid_type=pid_type), _external=True
                      )
            })
        return results

    def serialize_search(self, pid_fetcher, search_result, links=None,
                         item_links_factory=None, **kwargs):
        """Serialize a search result.

        :param pid_fetcher: Persistent identifier fetcher.
        :param search_result: Elasticsearch search result.
        :param links: Dictionary of links to add to response.
        """
        results = dict(
            hits=dict(
                hits=[self.transform_search_hit(
                    pid_fetcher(hit['_id'], hit['_source']),
                    hit,
                    links_factory=item_links_factory,
                    **kwargs
                ) for hit in search_result['hits']['hits']],
                total=search_result['hits']['total'],
            ),
            links=links or {},
            aggregations=search_result.get('aggregations', dict()),
        )
        return json.dumps(
            self.post_process_serialize_search(
                results, pid_fetcher), **self._format_args())


json_v1 = JSONSerializer(RecordSchemaJSONV1)
"""JSON v1 serializer."""

json_v1_search = search_responsify(json_v1, 'application/json')
json_v1_response = record_responsify(json_v1, 'application/json')
