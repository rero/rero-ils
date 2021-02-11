# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
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

"""Patrons serialization."""

from invenio_records_rest.serializers.response import search_responsify

from ..patron_types.api import PatronType
from ..serializers import JSONSerializer, RecordSchemaJSONV1


class PatronJSONSerializer(JSONSerializer):
    """Mixin serializing records as JSON."""

    def post_process_serialize_search(self, results, pid_fetcher):
        """Post process the search results."""
        # Add patron type name
        for type_term in results.get('aggregations', {}).get(
                'patron_type', {}).get('buckets', []):
            pid = type_term.get('key')
            name = PatronType.get_record_by_pid(pid).get('name')
            type_term['key'] = pid
            type_term['name'] = name

        return super().post_process_serialize_search(results, pid_fetcher)


json_patron = PatronJSONSerializer(RecordSchemaJSONV1)
"""JSON v1 serializer."""

json_patron_search = search_responsify(
    json_patron, 'application/rero+json')
