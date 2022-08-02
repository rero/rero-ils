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

"""RERO ILS record serialization."""
import inspect
from abc import ABC

from flask import json, request, url_for
from invenio_records_rest.serializers.json import \
    JSONSerializer as _JSONSerializer

from rero_ils.modules.documents.utils import filter_document_type_buckets


class CachedDataSerializerMixin:
    """Class to load and cached resources for serialization process."""

    def __init__(self):
        """Constructor."""
        self.clear_cache()

    def clear_cache(self):
        """Clear the resources cache."""
        self._resources = {}

    def get_resource(self, loader, pid):
        """Get a resource and store it into the cache if necessary.

        :param loader: Class use to retrieve the resource record.
        :param pid: the resource pid.
        :return: the requested resource.
        """
        cls_key = loader if inspect.isclass(loader) else loader.__class__
        convert_to_dict = not inspect.isclass(loader)  # AttrDict conversion
        if cls_key not in self._resources \
           or pid not in self._resources[cls_key]:
            resource = loader.get_record_by_pid(pid)
            if convert_to_dict:
                resource = resource.to_dict()
            self._resources.setdefault(cls_key, {})[pid] = resource
        return self._resources[cls_key][pid]


class PostprocessorMixinInterface(ABC):
    """Mixin postprocessing records during serialization."""

    def postprocess_serialize_search(self, results, pid_fetcher):
        """Post-process the search results.

        :param results: Search result.
        :param pid_fetcher: Persistent identifier fetcher.
        """
        raise NotImplementedError()


class PostprocessorMixin(PostprocessorMixinInterface):
    """Base class for post-processing record serializers."""

    def postprocess_serialize_search(self, results, pid_fetcher):
        """Post-process the search results.

        Post-processing a search result is a three steps process :
          1) allow modification on each search hit
          2) allow modification on aggregation buckets
          3) allow modification about links part

        :param results: Search result.
        :param pid_fetcher: Persistent identifier fetcher.
        """
        for hit in results.get('hits', {}).get('hits', []):
            self._postprocess_search_hit(hit)
        if aggregations := results.get('aggregations'):
            self._postprocess_search_aggregations(aggregations)
        self._postprocess_search_links(results, pid_fetcher)
        return results

    def _postprocess_search_links(self, search_results, pid_fetcher) -> None:
        """Post-process search links.

        :param search_results: Elasticsearch search result.
        :param pid_fetcher: Persistent identifier fetcher related to records
                            into the search result.
        """
        # add REST API to create a record related to the search result.
        pid_type = pid_fetcher(None, {'pid': '1'}).pid_type
        url = url_for(f'invenio_records_rest.{pid_type}_list', _external=True)
        search_results['links'].update({'create': url})

    def _postprocess_search_hit(self, hit: dict) -> None:
        """Post-process a specific search hit.

        :param hit: the dictionary representing an ElasticSearch search hit.
        """
        # DEV NOTES :
        #   Override this method in subclass to operate specific
        #   modification/enrichment on a search hit.

    def _postprocess_search_aggregations(self, aggregations: dict) -> None:
        """Post-process aggregations from a search result.

        :param aggregations: the dictionary representing ElasticSearch
                             aggregations section.
        """
        if 'document_type' in aggregations:
            aggr = aggregations['document_type'].get('buckets')
            filter_document_type_buckets(aggr)


class JSONSerializer(_JSONSerializer, PostprocessorMixin,
                     CachedDataSerializerMixin):
    """Serializer for RERO-ILS records as JSON."""

    def preprocess_record(self, pid, record, links_factory=None, **kwargs):
        """Prepare a record and persistent identifier for serialization."""
        rec = record
        if request and request.args.get('resolve') == '1':
            rec = record.replace_refs()
            # because the replace_refs loose the record original model. We need
            # to reset it to have correct 'created'/'updated' output data
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

    def serialize_search(self, pid_fetcher, search_result, links=None,
                         item_links_factory=None, **kwargs):
        """Serialize a search result.

        :param pid_fetcher: Persistent identifier fetcher.
        :param search_result: Elasticsearch search result.
        :param links: Dictionary of links to add to response.
        :param item_links_factory: Factory function for record links.
        """
        self.clear_cache()
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
