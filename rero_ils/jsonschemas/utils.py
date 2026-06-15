# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""JSON schemas utils."""

from invenio_jsonschemas.proxies import current_jsonschemas
from jsonresolver.contrib.jsonref import _JsonLoader

try:
    from functools import lru_cache
except ImportError:
    from functools32 import lru_cache


class JsonLoader(_JsonLoader):
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
        return (
            current_jsonschemas.get_schema(path=path)
            if (path := current_jsonschemas.url_to_path(uri))
            else super().get_remote_json(uri, **kwargs)
        )
