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

"""Acquisition account serialization."""

from rero_ils.modules.libraries.api import LibrariesSearch
from rero_ils.modules.serializers import ACQJSONSerializer, JSONSerializer

from ..api import AcqAccountsSearch


class AcqAccountJSONSerializer(ACQJSONSerializer):
    """Serializer for RERO-ILS `AcqAccount` records as JSON."""

    def preprocess_record(self, pid, record, links_factory=None, **kwargs):
        """Prepare a record and persistent identifier for serialization."""
        # Add some ES stored keys into response
        query = AcqAccountsSearch().filter('term', pid=record.pid).source()
        if hit := next(query.scan(), None):
            hit_metadata = hit.to_dict()
            keys = ['depth', 'distribution', 'is_active',
                    'encumbrance_exceedance', 'expenditure_exceedance',
                    'encumbrance_amount', 'expenditure_amount',
                    'remaining_balance']
            for key in keys:
                value = hit_metadata.get(key)
                if value is not None:
                    record[key] = value

        return super().preprocess_record(
            pid=pid,
            record=record,
            links_factory=links_factory,
            kwargs=kwargs
        )

    def _postprocess_search_aggregations(self, aggregations: dict) -> None:
        """Post-process aggregations from a search result."""
        JSONSerializer.enrich_bucket_with_data(
            aggregations.get('library', {}).get('buckets', []),
            LibrariesSearch, 'name'
        )
        super()._postprocess_search_aggregations(aggregations)
