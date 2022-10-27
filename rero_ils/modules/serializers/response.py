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

"""Serialization response factories.

Responsible for creating an HTTP response given the output of a serializer.
"""
from __future__ import absolute_import, print_function

from datetime import datetime

from flask import current_app
from invenio_records_rest.serializers.response import add_link_header


def search_responsify(serializer, mimetype):
    """Create a Records-REST search result response serializer.

    .. note::
        Why rewrite a custom 'search_responsify' function instead of using
        function from ``invenio_records_rest.serializers.response`` ?

        The Invenio core function create a single serializer object when the
        application is loaded. This object if reused for any requests. But
        in our case, sometimes, we use a ``CachedDataSerializerMixin``. If the
        cache is never reset, any changes on a resource already in the cache
        were never applied during application instance life.
        To solve this problem, in our custom function, we use a new
        serializer for each call. In this way, the cache is always empty at the
        beginning of any serialization.

    :param serializer: Serializer instance.
    :param mimetype: MIME type of response.
    :returns: Function that generates a record HTTP response.
    """
    def view(pid_fetcher, search_result, code=200, headers=None, links=None,
             item_links_factory=None):
        # Check if the serializer implement a 'reset' function. If yes, then
        # call this function before perform serialization.
        if (reset := getattr(serializer, 'reset', None)) and callable(reset):
            reset()
        response = current_app.response_class(
            serializer.serialize_search(
                pid_fetcher, search_result,
                links=links, item_links_factory=item_links_factory),
            mimetype=mimetype)
        response.status_code = code
        if headers is not None:
            response.headers.extend(headers)
        if links is not None:
            add_link_header(response, links)
        return response
    return view


def search_responsify_file(serializer, mimetype, file_extension,
                           file_prefix=None, file_suffix=None):
    """Create a Records-REST search result response serializer.

    :param serializer: Serializer instance.
    :param mimetype: MIME type of response.
    :param file_extension: File extension.
    :returns: Function that generates a record HTTP response.
    """

    def view(pid_fetcher, search_result, code=200, headers=None, links=None,
             item_links_factory=None):
        response = current_app.response_class(
            serializer.serialize_search(
                pid_fetcher, search_result,
                links=links,
                item_links_factory=item_links_factory
            ),
            mimetype=mimetype
        )
        response.status_code = code
        if headers is not None:
            response.headers.extend(headers)

        tstamp = datetime.today().strftime('%Y%m%d')
        parts = filter(None, [file_prefix, tstamp, file_suffix])
        filename = '-'.join(parts) + '.' + file_extension
        if not response.headers.get('Content-Disposition'):
            response.headers['Content-Disposition'] = \
                f'attachment; filename="{filename}"'

        if links is not None:
            add_link_header(response, links)

        return response

    return view


def record_responsify_file(serializer, mimetype, file_extension,
                           file_prefix=None, file_suffix=None):
    """Create a Records-REST search result response serializer.

    :param serializer: Serializer instance.
    :param mimetype: MIME type of response.
    :param file_extension: File extension.
    :returns: Function that generates a record HTTP response.
    """
    def view(pid, record, code=200, headers=None, links_factory=None):
        response = current_app.response_class(
            serializer.serialize(pid, record, links_factory=links_factory),
            mimetype=mimetype)
        response.status_code = code
        response.cache_control.no_cache = True
        response.set_etag(str(record.revision_id))
        response.last_modified = record.updated
        if headers is not None:
            response.headers.extend(headers)

        tstamp = datetime.today().strftime('%Y%m%d')
        parts = filter(None, [file_prefix, tstamp, file_suffix])
        filename = '-'.join(parts) + '.' + file_extension
        if not response.headers.get('Content-Disposition'):
            response.headers['Content-Disposition'] = \
                f'attachment; filename="{filename}"'

        if links_factory is not None:
            add_link_header(response, links_factory(pid))

        return response

    return view
