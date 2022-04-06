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

"""Serialization response factories.

Responsible for creating a HTTP response given the output of a serializer.
"""
from __future__ import absolute_import, print_function

from datetime import datetime

import pytz
from flask import current_app
from invenio_records_rest.serializers.response import add_link_header


def search_responsify_file(serializer, mimetype, file_extension):
    """Create a Records-REST search result response serializer.

    :param serializer: Serializer instance.
    :param mimetype: MIME type of response.
    :param file_extension: File extension.
    :returns: Function that generates a record HTTP response.
    """

    def view(pid_fetcher, search_result, code=200, headers=None, links=None,
             item_links_factory=None):
        response = current_app.response_class(
            serializer.serialize_search(pid_fetcher, search_result,
                                        links=links,
                                        item_links_factory=item_links_factory),
            mimetype=mimetype)
        response.status_code = code
        if headers is not None:
            response.headers.extend(headers)
        timezone = current_app.config.get('BABEL_DEFAULT_TIMEZONE')
        date = datetime.now(tz=pytz.timezone(timezone)).strftime('%Y%m%d')
        file_name = f'export-{date}.{file_extension}'
        if not response.headers.get('Content-Disposition'):
            response.headers['Content-Disposition'] = \
                f'attachment; filename="{file_name}"'
        if links is not None:
            add_link_header(response, links)

        return response

    return view
