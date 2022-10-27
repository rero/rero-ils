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

"""Acquisition order serialization."""

from rero_ils.modules.acquisition.acq_accounts.api import AcqAccountsSearch
from rero_ils.modules.acquisition.budgets.api import BudgetsSearch
from rero_ils.modules.libraries.api import LibrariesSearch
from rero_ils.modules.serializers import ACQJSONSerializer, JSONSerializer
from rero_ils.modules.vendors.api import VendorsSearch


class AcqOrderJSONSerializer(ACQJSONSerializer):
    """Mixin serializing records as JSON."""

    def _postprocess_search_aggregations(self, aggregations: dict) -> None:
        """Post-process aggregations from a search result."""
        JSONSerializer.enrich_bucket_with_data(
            aggregations.get('library', {}).get('buckets', []),
            LibrariesSearch, 'name'
        )
        JSONSerializer.enrich_bucket_with_data(
            aggregations.get('vendor', {}).get('buckets', []),
            VendorsSearch, 'name'
        )
        JSONSerializer.enrich_bucket_with_data(
            aggregations.get('account', {}).get('buckets', []),
            AcqAccountsSearch, 'name'
        )
        JSONSerializer.enrich_bucket_with_data(
            aggregations.get('budget', {}).get('buckets', []),
            BudgetsSearch, 'name'
        )
        # Add configuration for order_date and receipt_date buckets
        for aggr_name in ['order_date', 'receipt_date']:
            aggr = aggregations.get(aggr_name, {})
            JSONSerializer.add_date_range_configuration(aggr)

        super()._postprocess_search_aggregations(aggregations)
