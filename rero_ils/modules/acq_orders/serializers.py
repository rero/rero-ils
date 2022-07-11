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

"""Acquisition order serialization."""

from invenio_records_rest.serializers.response import record_responsify, \
    search_responsify

from rero_ils.modules.acq_accounts.api import AcqAccountsSearch
from rero_ils.modules.libraries.api import LibrariesSearch
from rero_ils.modules.serializers import ACQJSONSerializer, RecordSchemaJSONV1
from rero_ils.modules.vendors.api import VendorsSearch


class AcqOrderJSONSerializer(ACQJSONSerializer):
    """Mixin serializing records as JSON."""

    def _postprocess_search_aggregations(self, aggregations: dict) -> None:
        """Post-process aggregations from a search result."""
        self.enrich_bucket_with_data(
            aggregations.get('library', {}).get('buckets', []),
            LibrariesSearch, 'name'
        )
        self.enrich_bucket_with_data(
            aggregations.get('vendor', {}).get('buckets', []),
            VendorsSearch, 'name'
        )
        self.enrich_bucket_with_data(
            aggregations.get('account', {}).get('buckets', []),
            AcqAccountsSearch, 'name'
        )
        # Add configuration for order_date and receipt_date buckets
        for aggr_name in ['order_date', 'receipt_date']:
            aggr = aggregations.get(aggr_name)
            if not aggr:
                continue
            if values := [term['key'] for term in aggr.get('buckets', [])]:
                aggregations[aggr_name]['type'] = 'date-range'
                aggregations[aggr_name]['config'] = {
                    'min': min(values),
                    'max': max(values),
                    'step': 86400000  # 1 day in millis
                }
        super()._postprocess_search_aggregations(aggregations)


_json = AcqOrderJSONSerializer(RecordSchemaJSONV1)
json_acor_search = search_responsify(_json, 'application/rero+json')
json_acor_record = record_responsify(_json, 'application/rero+json')
