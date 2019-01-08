# -*- coding: utf-8 -*-
#
# This file is part of RERO ILS.
# Copyright (C) 2017 RERO.
#
# RERO ILS is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# RERO ILS is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RERO ILS; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Record serialization."""

from flask import current_app, json
from invenio_records_rest.schemas import RecordSchemaJSONV1
from invenio_records_rest.serializers.response import search_responsify

from ..libraries.api import Library
from ..serializers import ReroIlsSerializer


class ReroIlsSerializer(ReroIlsSerializer):
    """Mixin serializing records as JSON."""

    def serialize_search(self, pid_fetcher, search_result, links=None,
                         item_links_factory=None, **kwargs):
        """Serialize a search result.

        :param pid_fetcher: Persistent identifier fetcher.
        :param search_result: Elasticsearch search result.
        :param links: Dictionary of links to add to response.
        """
        results = dict(
            hits=dict(
                hits=[self.transform_search_hit(
                    pid_fetcher(hit['_id'], hit['_source']),
                    hit,
                    links_factory=item_links_factory,
                    **kwargs
                ) for hit in search_result['hits']['hits']],
                total=search_result['hits']['total'],
            ),
            links=links or {},
            aggregations=search_result.get('aggregations', dict()),
        )
        with current_app.app_context():
            facet_config = current_app.config.get(
                'RERO_ILS_APP_CONFIG_FACETS', {}
            )
            try:
                type = search_result['hits']['hits'][0]['_index'].split('-')[0]
                for aggregation in results.get('aggregations'):
                    facet_config_type = facet_config.get(type, {})
                    facet_config_type_expand = facet_config_type.get(
                        'expand', ''
                    )
                    results['aggregations'][aggregation]['expand'] = False
                    if aggregation in facet_config_type_expand:
                        results['aggregations'][aggregation]['expand'] = True
                for lib_term in results.get('aggregations', {}).get(
                        'library', {}).get('buckets', []):
                    pid = lib_term.get('key')
                    name = Library.get_record_by_pid(pid).get('name')
                    lib_term['name'] = name
            except Exception:
                pass
        return json.dumps(results, **self._format_args())


json_doc = ReroIlsSerializer(RecordSchemaJSONV1)
"""JSON v1 serializer."""

json_doc_search = search_responsify(json_doc, 'application/rero+json')
# json_v1_response = record_responsify(json_v1, 'application/rero+json')
