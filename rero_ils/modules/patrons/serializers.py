# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
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

from rero_ils.modules.patron_types.api import PatronTypesSearch
from rero_ils.modules.serializers import JSONSerializer, RecordSchemaJSONV1, \
    search_responsify


class PatronJSONSerializer(JSONSerializer):
    """Serializer for RERO-ILS `Patron` records as JSON."""

    def _postprocess_search_aggregations(self, aggregations: dict) -> None:
        """Post-process aggregations from a search result."""
        JSONSerializer.enrich_bucket_with_data(
            aggregations.get('patron_type', {}).get('buckets', []),
            PatronTypesSearch, 'name'
        )
        super()._postprocess_search_aggregations(aggregations)


_json = PatronJSONSerializer(RecordSchemaJSONV1)
json_patron_search = search_responsify(_json, 'application/rero+json')
