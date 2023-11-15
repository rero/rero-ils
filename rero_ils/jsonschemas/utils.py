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

"""JSON schemas utils."""

from invenio_jsonschemas.proxies import current_jsonschemas
from jsonref import URIDict

try:
    from functools import lru_cache
except ImportError:
    from functools32 import lru_cache


class JsonLoader(object):
    """JsonLoader.

    Provides a callable which takes a URI, and returns the loaded JSON referred
    to by that URI. Uses :mod:`requests` if available for HTTP URIs, and falls
    back to :mod:`urllib`. By default it keeps a cache of previously loaded
    documents.
    :param store: A pre-populated dictionary matching URIs to loaded JSON
        documents
    :param cache_results: If this is set to false, the internal cache of
        loaded JSON documents is not used
    """

    def __init__(self, store=(), cache_results=True):
        """Constructor."""
        self.store = URIDict(store)
        self.cache_results = cache_results

    def __call__(self, uri, **kwargs):
        """Call.

        Return the loaded JSON referred to by `uri`
        :param uri: The URI of the JSON document to load
        :param kwargs: Keyword arguments passed to :func:`json.loads`
        """
        if uri in self.store:
            return self.store[uri]
        result = self.get_remote_json(uri, **kwargs)
        if self.cache_results:
            self.store[uri] = result
        return result

    @lru_cache(maxsize=1000)
    def get_remote_json(self, uri, **kwargs):
        """Get remote json.

        We have to add local $ref loading to the base class.
        https://invenio-jsonschemas.readthedocs.io/en/latest/configuration.html

        Adds loading of $ref locally for the application instance.
        See: github invenio-jsonschemas ext.py.
        :param uri: The URI of the JSON document to load.
        :param kwargs: Keyword arguments passed to json.loads().
        :returns: resolved json schema.
        """
        path = current_jsonschemas.url_to_path(uri)
        if path:
            result = current_jsonschemas.get_schema(path=path)
        else:
            result = super().get_remote_json(uri, **kwargs)
        return result
