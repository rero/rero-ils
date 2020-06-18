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

"""Import serialization."""

from datetime import datetime

from flask import current_app, json
from invenio_records_rest.schemas import RecordSchemaJSONV1
from invenio_records_rest.serializers.json import JSONSerializer
from invenio_records_rest.serializers.response import add_link_header, \
    search_responsify
from marshmallow import fields

from ..documents.api import Document
from ..documents.dojson.contrib.unimarctojson import unimarc
from ..documents.utils import title_format_text_head


def record_responsify(serializer, mimetype):
    """Create a Records-REST response serializer.

    :param serializer: Serializer instance.
    :param mimetype: MIME type of response.
    :returns: Function that generates a record HTTP response.
    """
    def view(pid, record, code=200, headers=None, links_factory=None):
        response = current_app.response_class(
            serializer.serialize(pid, record, links_factory=links_factory),
            mimetype=mimetype)
        response.status_code = code
        # TODO: do we have to set an etag?
        # response.set_etag('xxxxx')
        response.last_modified = datetime.now()
        if headers is not None:
            response.headers.extend(headers)

        if links_factory is not None:
            add_link_header(response, links_factory(pid))

        return response

    return view


class ImportSchemaJSONV1(RecordSchemaJSONV1):
    """Schema for import records RERO ILS in JSON.

    Add a permissions field.
    """

    permissions = fields.Raw()
    explanation = fields.Raw()


class ImportsSearchSerializer(JSONSerializer):
    """Mixin serializing records as JSON."""

    def serialize_search(self, pid_fetcher, search_result, links=None,
                         item_links_factory=None, **kwargs):
        """Serialize a search result.

        :param pid_fetcher: Persistent identifier fetcher.
        :param search_result: Elasticsearch search result.
        :param links: Dictionary of links to add to response.
        """
        for hit in search_result['hits']['hits']:
            hit['metadata'] = self.post_process(hit['metadata'])
            hit['metadata']['pid'] = hit['id']
        results = dict(
            hits=dict(
                hits=search_result['hits']['hits'],
                total=search_result['hits']['total'],
                remote_total=search_result['hits']['remote_total'],
            ),
            aggregations=search_result.get('aggregations', dict()),
        )
        return json.dumps(results, **self._format_args())

    def post_process(self, metadata):
        """Post process the data.

        hook to be redefined in a child class.

        :param metadata: dictionary version of a record
        :return: the modified dictionary
        """
        return metadata

    def serialize(self, pid, record, links_factory=None, **kwargs):
        """Serialize a single record.

        :param pid: Persistent identifier instance.
        :param search_result: Elasticsearch search result.
        :param links: Dictionary of links to add to response.
        """
        return json.dumps(
            dict(metadata=self.post_process(unimarc.do(record))),
            **self._format_args())


class UIImportsSearchSerializer(ImportsSearchSerializer):
    """Serializing records as JSON with additional data."""

    def post_process(self, metadata):
        """Post process the data.

        add extra data such as title statement.

        :param metadata: dictionary version of a record
        :return: the modified dictionary
        """
        metadata = Document.post_process(metadata)

        titles = metadata.get('title', [])
        text_title = title_format_text_head(titles, with_subtitle=False)
        if text_title:
            metadata['ui_title_text'] = text_title
        responsibility = metadata.get('responsibilityStatement', [])
        text_title = title_format_text_head(titles, responsibility,
                                            with_subtitle=False)
        if text_title:
            metadata['ui_title_text_responsibility'] = text_title
        return metadata


class ImportsMarcSearchSerializer(JSONSerializer):
    """Mixin serializing records as JSON."""

    def serialize(self, pid, record, links_factory=None, **kwargs):
        """Serialize a single record.

        :param pid: Persistent identifier instance.
        :param search_result: Elasticsearch search result.
        :param links: Dictionary of links to add to response.
        """
        def sort_ordered_dict(ordered_dict):
            res = []
            for key, value in ordered_dict.items():
                if key != '__order__':
                    if len(key) == 5:
                        key = '{tag} {ind}'.format(tag=key[:3], ind=key[3:])
                    if isinstance(value, dict):
                        res.append([key, sort_ordered_dict(value)])
                    else:
                        if isinstance(value, (tuple, list)):
                            for val in value:
                                if isinstance(val, dict):
                                    res.append([key, sort_ordered_dict(val)])
                                else:
                                    res.append([key, val])
                        else:
                            res.append([key, value])
            return res

        return json.dumps(sort_ordered_dict(record), **self._format_args())


json_v1_search = ImportsSearchSerializer(ImportSchemaJSONV1)
json_v1_record = ImportsSearchSerializer(ImportSchemaJSONV1)
json_v1_uisearch = UIImportsSearchSerializer(ImportSchemaJSONV1)
json_v1_uirecord = UIImportsSearchSerializer(ImportSchemaJSONV1)
json_v1_record_marc = ImportsMarcSearchSerializer(ImportSchemaJSONV1)

json_v1_import_search = search_responsify(json_v1_search,
                                          'application/json')
json_v1_import_record = record_responsify(json_v1_record,
                                          'application/json')
json_v1_import_uisearch = search_responsify(json_v1_uisearch,
                                            'application/rero+json')
json_v1_import_uirecord = record_responsify(json_v1_uirecord,
                                            'application/rero+json')
json_v1_import_record_marc = record_responsify(json_v1_record_marc,
                                               'application/json+marc')
