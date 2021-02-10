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

"""Patron transactions serialization."""

from invenio_records_rest.serializers.response import search_responsify

from rero_ils.modules.serializers import JSONSerializer, RecordSchemaJSONV1

from ..libraries.api import Library


class PatronTransactionEventsJSONSerializer(JSONSerializer):
    """Mixin serializing records as JSON."""

    def post_process_serialize_search(self, results, pid_fetcher):
        """Post process the search results."""
        records = results.get('hits', {}).get('hits', {})
        for record in records:
            metadata = record.get('metadata', {})
            # Library
            library_pid = metadata.get('library', {}).get('pid')
            if library_pid:
                library = Library.get_record_by_pid(library_pid)
                metadata['library']['name'] = library.get('name')
        return super(PatronTransactionEventsJSONSerializer, self)\
            .post_process_serialize_search(results, pid_fetcher)


json_patron_transaction_events = \
    PatronTransactionEventsJSONSerializer(RecordSchemaJSONV1)
"""JSON v1 serializer."""

json_patron_transaction_events_search = search_responsify(
    json_patron_transaction_events, 'application/rero+json')
