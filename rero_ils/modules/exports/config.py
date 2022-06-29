# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2022 RERO
# Copyright (C) 2022 UCLouvain
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

"""RERO ILS export module configuration file."""

"""
  This module must be used to create dynamic export route for resource
  configured by the `invenio-records-rest`. Exports endpoints will provide
  streamed content. The content is based on an ElasticSearch search result ;
  this result is processed using ElasticSearch `scan()` method tu fully
  implement streamed result.

  Each configured endpoint add a flask blueprint endpoint accessible using the
  `/export/{resource_list_route/` url.
"""

RECORDS_REST_ENDPOINTS = dict(
    resource=dict(
        # See: https://github.com/inveniosoftware/invenio-records-rest/blob/
        #      master/invenio_records_rest/config.py
    )
)

RERO_EXPORT_REST_ENDPOINTS = dict(
    loan=dict(
        resource=RECORDS_REST_ENDPOINTS.get('resource'),
        default_media_type='text/csv',
        search_serializers={
            'text/csv': 'rero_ils.modules.loans.serializers:csv_stream_search',
        },
        search_serializers_aliases={
            'csv': 'text/csv'
        }
    )
)

"""
.. code-block:: python

RERO_EXPORT_REST_ENDPOINTS = dict(
    loan=dict(
        resource={invenio-record-rest_resource_configuration_endpoint},
        default_media_type='text/csv',
        search_serializers={
            'text/csv': 'rero_ils.modules.loans.serializers:csv_stream_search',
        },
        search_serializers_aliases={
            'csv': 'text/csv'
        }
    )
)

:param resource: Pointer to the resource rest configuration endpoint from
    `invenio-record-rest`. Check `https://github.com/inveniosoftware/invenio-
    records-rest/blob/master/invenio_records_rest/config.py` to get correct
    resource configuration.

:param search_serializers: It contains the list of records serializers for all
    supported format. This configuration differ from the previous because in
    this case it handle a list of records resulted by a search query instead of
    a single record.

:param search_serializers_aliases: A mapping of values of the defined query arg
    (see `config.REST_MIMETYPE_QUERY_ARG_NAME`) to valid mimetypes for records
    search serializers: dict(alias -> mimetype).

"""
