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
import inspect
from abc import ABC

from flask import url_for
from invenio_search import RecordsSearch

from rero_ils.modules.documents.utils import filter_document_type_buckets


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
            # special process for nested aggregations
            #   to display the results of nested aggregations
            #   (nested aggregations are created to apply facet filters),
            #   put the value of the nested 'aggs_facet' aggregation
            #   one level up.
            for key, agg in aggregations.items():
                if agg and ('aggs_facet' in agg):
                    aggregations[key] = aggregations[key]['aggs_facet']
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


class CachedDataSerializerMixin:
    """Class to load and cached resources for serialization process."""

    def __init__(self, limit=2000):
        """Init.

        :param limit: the maximum number of element to keep in cache.
        :raises AssertionError: limit is lower or equal to 0.
        """
        # TODO :: Use variable from config but this will conflict all tests
        #    because appcontext is missing
        assert limit > 0
        self._resources = {}
        self._limit = limit

    def reset(self):
        """Resetting the cache."""
        self._resources.clear()

    def append(self, key, resource):
        """Append a resource into the cache.

        If the cache reached the limit, then the first older element of the
        cache will be removed to free space to this resource.

        :param key: the resource key.
        :param resource: the resource to add to the cache.
        """
        if len(self._resources) >= self._limit:
            # remove the first element from dict. Not sure that this is the
            # order element of the dictionary, but it should.
            (k := next(iter(self._resources)), self._resources.pop(k))
        self._resources[key] = resource

    @staticmethod
    def _get_key(loader, pid):
        """Get the key where store the resource.

        :param loader: Class use to retrieve the resource records.
        :return: The key where store the resource into the cache.
        """
        if not inspect.isclass(loader):
            loader = loader.__class__
        return hash(loader.__name__ + pid)

    def load_all(self, *args):
        """Load all resources and store them into the cache.

        :param args: Classes use to retrieve the resource records. Each class
            should be a ``invenio_search.api.RecordsSearch`` subclass to get
            records from the ElasticSearch index.
        :raises AssertionError if a loader class isn't
            ``invenio_search.api.RecordsSearch`` subclass.
        """
        for loader in args:
            assert issubclass(loader.__class__, RecordsSearch)
            for hit in loader.scan():
                pid = hit['pid']
                key = CachedDataSerializerMixin._get_key(loader, pid)
                self.append(key, hit.to_dict())

    def load_resources(self, loader, pids):
        """Load a set of resource and store them into the cache.

        :param loader: Class use to retrieve the resource records.
        :param pids: List of pids to load.
        """
        assert type(pids) is list
        resources = []
        for resource in loader.get_records_by_pids(pids):
            if not inspect.isclass(loader):  # AttrDict conversion
                resource = resource.to_dict()
            if pid := resource.get('pid'):
                key = CachedDataSerializerMixin._get_key(loader, pid)
                self.append(key, resource)
                resources.append(resource)
        return resources

    def get_resource(self, loader, pid):
        """Get a resource and store it into the cache if necessary.

        :param loader: Class use to retrieve the resource record.
        :param pid: the resource pid.
        :return: the requested resource.
        """
        resource_key = CachedDataSerializerMixin._get_key(loader, pid)
        if resource_key in self._resources:
            return self._resources[resource_key]
        return next(iter(self.load_resources(loader, [pid])), None)


class StreamSerializerMixin:
    """Utility class to deal with streamed result response (ES.scan())."""

    """ The default chunk size to use. This attribute can be override."""
    chunk_size = 1000

    @classmethod
    def get_chunks(cls, results):
        """Get results as list of chunk.

        Note:
          Using chunked list is usefully if you need to enrich current result
          hits with outside data. For example: reading a list 2400 loans with
          a chunk_size=1000, you will get 3 chunks (1000, 1000, 400). For each
          chunk, you could extract the list of related document pids and call
          once ES document index to get document data ==> 3 calls to document
          index instead of potentially 2400 (much better).

        :param results: the result iterator to process.
        :returns: a generator of chunked results. Each result is a tuple of
          `hit.pid` and `hit`.
        """
        pids, records = [], []
        for result in results:
            pids.append(result.pid)
            records.append(result)
            if len(records) % cls.chunk_size == 0:
                yield pids, records
                pids.clear()
                records.clear()
        yield pids, records
