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

"""RERO ILS record serialization."""

from copy import deepcopy

import pytz
from flask import json, request
from invenio_jsonschemas import current_jsonschemas
from invenio_records_rest.serializers.json import \
    JSONSerializer as _JSONSerializer

from .mixins import PostprocessorMixin


def schema_from_context(_, context, data, schema):
    """Get the record's schema from context."""
    record = (context or {}).get('record', {})
    return record.get('$schema', current_jsonschemas.path_to_url(schema))


class JSONSerializer(_JSONSerializer, PostprocessorMixin):
    """Serializer for RERO-ILS records as JSON."""

    def preprocess_record(self, pid, record, links_factory=None, **kwargs):
        """Prepare a record and persistent identifier for serialization."""
        links_factory = links_factory or (lambda x, record=None, **k: dict())
        if request and request.args.get('resolve') == '1':
            metadata = record.resolve()
            # if not enable jsonref the dumps is already done in the resolve
            # method
            if getattr(record, 'enable_jsonref', False):
                metadata = metadata.dumps()
        else:
            metadata = deepcopy(record.replace_refs()) if self.replace_refs \
                else record.dumps()
        return dict(
            pid=pid,
            metadata=metadata,
            links=links_factory(pid, record=record, **kwargs),
            revision=record.revision_id,
            created=(pytz.utc.localize(record.created).isoformat()
                     if record.created else None),
            updated=(pytz.utc.localize(record.updated).isoformat()
                     if record.updated else None),
        )

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

    def serialize_search(self, pid_fetcher, search_result, links=None,
                         item_links_factory=None, **kwargs):
        """Serialize a search result.

        :param pid_fetcher: Persistent identifier fetcher.
        :param search_result: Elasticsearch search result.
        :param links: Dictionary of links to add to response.
        :param item_links_factory: Factory function for record links.
        """
        results = dict(
            hits=dict(
                hits=[
                    self.transform_search_hit(
                        pid_fetcher(hit['_id'], hit['_source']),
                        hit, links_factory=item_links_factory, **kwargs)
                    for hit in search_result['hits']['hits']
                ],
                total=search_result['hits']['total'],
            ),
            links=links or {},
            aggregations=search_result.get('aggregations', dict()),
        )
        return json.dumps(
            self.postprocess_serialize_search(results, pid_fetcher),
            **self._format_args()
        )

    @staticmethod
    def enrich_bucket_with_data(buckets, search_cls, attributes_name):
        """Complete a bucket by adding new keys based on resource attributes.

        :param buckets: the buckets (aggregation set) to perform.
        :param search_cls: the search class related to the resource to resolve.
        :param attributes_name: attributes to load from search data.
        """
        attributes_name = attributes_name or []
        if not isinstance(attributes_name, list):
            attributes_name = [attributes_name]
        # search all requested values using search class
        query = search_cls() \
            .filter('terms', pid=[term['key'] for term in buckets]) \
            .source(['pid'] + attributes_name)
        data = {result.pid: result.to_dict() for result in query.scan()}
        # complete buckets with data
        for term in buckets:
            for attr in attributes_name:
                if attr in data[term['key']]:
                    term[attr] = data[term['key']].get(attr)

    @staticmethod
    def add_date_range_configuration(aggregation, step=86400000):
        """Add a configuration block for date buckets.

        :param aggregation: the aggregation to process.
        :param step: the number of millis for each step. By default : 1 day.
        """
        if values := [term['key'] for term in aggregation.get('buckets', [])]:
            aggregation['type'] = 'date-range'
            aggregation['config'] = {
                'min': min(values),
                'max': max(values),
                'step': step  # 1 day in millis
            }


class ACQJSONSerializer(JSONSerializer, PostprocessorMixin):
    """Serializer for RERO-ILS acquisition records as JSON."""

    def preprocess_record(self, pid, record, links_factory=None, **kwargs):
        """Prepare a record and persistent identifier for serialization."""
        # add some dynamic key related to the record.
        record['is_current_budget'] = record.is_active
        return super().preprocess_record(
            pid=pid, record=record, links_factory=links_factory, kwargs=kwargs)
