# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Import serialization."""

from datetime import datetime

from flask import current_app
from invenio_records_rest.serializers.response import add_link_header


def record_responsify(serializer, mimetype, dojson_class=None):
    """Create a Records-REST response serializer.

    :param serializer: Serializer instance.
    :param mimetype: MIME type of response.
    :return: Function that generates a record HTTP response.
    """

    def view(pid, record, code=200, headers=None, links_factory=None):
        response = current_app.response_class(
            serializer.serialize(pid, record, links_factory=links_factory, dojson_class=dojson_class),
            mimetype=mimetype,
        )
        response.status_code = code
        # TODO: do we have to set an etag?
        # response.set_etag('xxxxx')
        response.last_modified = datetime.now()
        if headers:
            response.headers.extend(headers)

        if links_factory:
            add_link_header(response, links_factory(pid))

        return response

    return view
