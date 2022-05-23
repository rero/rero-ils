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

from rero_ils.modules.acq_accounts.api import AcqAccount
from rero_ils.modules.libraries.api import Library
from rero_ils.modules.serializers import JSONSerializer
from rero_ils.modules.vendors.api import Vendor


class AcqOrderJSONSerializer(JSONSerializer):
    """Mixin serializing records as JSON."""

    def post_process_serialize_search(self, results, pid_fetcher):
        """Post process the search results."""
        # Adding info into buckets
        JSONSerializer.complete_bucket_with_attribute(
            results, 'library', Library, 'name')
        JSONSerializer.complete_bucket_with_attribute(
            results, 'vendor', Vendor, 'name')
        JSONSerializer.complete_bucket_with_attribute(
            results, 'account', AcqAccount, 'name')

        # Add configuration for order_date and receipt_date buckets
        for bucket in ['order_date', 'receipt_date']:
            aggr = results['aggregations'].get(bucket)
            if not aggr:
                continue
            bucket_values = [term['key'] for term in aggr.get('buckets', [])]
            if bucket_values:
                results['aggregations'][bucket]['type'] = 'date-range'
                results['aggregations'][bucket]['config'] = {
                    'min': min(bucket_values),
                    'max': max(bucket_values),
                    'step': 86400000  # 1 day in millis
                }

        return super().post_process_serialize_search(results, pid_fetcher)
