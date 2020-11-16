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

"""ILL Request serialization."""

from invenio_records_rest.serializers.response import search_responsify

from ..libraries.api import Library
from ..serializers import JSONSerializer, RecordSchemaJSONV1


class ILLRequestJSONSerializer(JSONSerializer):
    """Mixin serializing records as JSON."""

    def post_process_serialize_search(self, results, pid_fetcher):
        """Post process the search results."""
        aggrs = results.get('aggregations', {})
        # replace the library pid by the library name for faceting
        for lib_term in aggrs.get('library', {}).get('buckets', []):
            pid = lib_term.get('key')
            lib_term['name'] = Library.get_record_by_pid(pid).get('name')

        return super().post_process_serialize_search(results, pid_fetcher)


json_ill_request = ILLRequestJSONSerializer(RecordSchemaJSONV1)
json_ill_request_search = search_responsify(json_ill_request,
                                            'application/rero+json')
