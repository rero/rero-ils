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

"""Document serialization."""

from flask import current_app, request
from invenio_records_rest.serializers.response import search_responsify

from ..libraries.api import Library
from ..organisations.api import Organisation
from ..serializers import JSONSerializer, RecordSchemaJSONV1


class DocumentJSONSerializer(JSONSerializer):
    """Mixin serializing records as JSON."""

    def post_process_serialize_search(self, results, pid_fetcher):
        """Post process the search results."""
        # Item filters.
        viewcode = request.args.get('view')
        if viewcode != current_app.config.get(
            'RERO_ILS_SEARCH_GLOBAL_VIEW_CODE'
        ):
            view_id = Organisation.get_record_by_viewcode(viewcode)['pid']
            records = results.get('hits', {}).get('hits', {})
            for record in records:
                metadata = record.get('metadata', {})
                items = metadata.get('items', [])
                if items:
                    output = []
                    for item in items:
                        if item.get('organisation')\
                                .get('organisation_pid') == view_id:
                            output.append(item)
                    record['metadata']['items'] = output

        # Add organisation name
        for org_term in results.get('aggregations', {}).get(
                'organisation', {}).get('buckets', []):
            pid = org_term.get('key')
            name = Organisation.get_record_by_pid(pid).get('name')
            org_term['name'] = name

        # Add library name
        for lib_term in results.get('aggregations', {}).get(
                'library', {}).get('buckets', []):
            pid = lib_term.get('key').split('-')[1]
            name = Library.get_record_by_pid(pid).get('name')
            lib_term['key'] = pid
            lib_term['name'] = name

        return super(
            DocumentJSONSerializer, self).post_process_serialize_search(
                results, pid_fetcher)


json_doc = DocumentJSONSerializer(RecordSchemaJSONV1)
"""JSON v1 serializer."""

json_doc_search = search_responsify(json_doc, 'application/rero+json')
