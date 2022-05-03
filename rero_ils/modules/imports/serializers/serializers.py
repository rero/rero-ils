# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
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

from flask import json
from invenio_records_rest.schemas import RecordSchemaJSONV1
from invenio_records_rest.serializers.json import JSONSerializer
from jsonref import JsonRef
from marshmallow import fields

from rero_ils.modules.documents.api import Document
from rero_ils.modules.documents.dojson.contrib.marc21tojson.rero import marc21
from rero_ils.modules.documents.utils import create_contributions, \
    title_format_text_head


class ImportSchemaJSONV1(RecordSchemaJSONV1):
    """Schema for import records RERO ILS in JSON.

    Add a permissions field.
    """

    permissions = fields.Raw()
    explanation = fields.Raw()


class ImportsSearchSerializer(JSONSerializer):
    """Mixin serializing records as JSON."""

    def __init__(self, *args, **kwargs):
        """Constructor."""
        self.record_processor = kwargs.pop("record_processor", marc21.do)
        super(JSONSerializer, self).__init__(*args, **kwargs)

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
                total=search_result['hits']['total']['value'],
                remote_total=search_result['hits']['remote_total'],
            ),
            aggregations=search_result.get('aggregations', dict()),
        )
        # TODO: If we have multiple types for a document we have to Correct
        # the document type buckets here.
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
            dict(metadata=self.post_process(
                self.record_processor(record))),
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
        contributions = metadata.get('contribution', [])
        new_contributions = []
        for contribution in contributions:
            agent = contribution['agent']
            agent_type = agent['type']
            agent_data = JsonRef.replace_refs(
                agent, loader=None).get('metadata')
            if agent_data:
                agent_data.pop('$schema', None)
                agent = agent_data
                agent['type'] = agent_type
            new_contributions.append({'agent': agent})
        if new_contributions:
            metadata['contribution'] = create_contributions(new_contributions)
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
