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

"""Acquisition invoice serialization."""

from invenio_records_rest.serializers.response import record_responsify

from rero_ils.modules.libraries.api import LibrariesSearch
from rero_ils.modules.serializers import (
    ACQJSONSerializer,
    JSONSerializer,
    RecordSchemaJSONV1,
    search_responsify,
)


class AcquisitionInvoiceJSONSerializer(ACQJSONSerializer):
    """Serializer for RERO-ILS `AcqInvoice` records as JSON."""

    def _postprocess_search_aggregations(self, aggregations: dict) -> None:
        """Post-process aggregations from a search result."""
        JSONSerializer.enrich_bucket_with_data(
            aggregations.get("library", {}).get("buckets", []), LibrariesSearch, "name"
        )
        super()._postprocess_search_aggregations(aggregations)


_json = AcquisitionInvoiceJSONSerializer(RecordSchemaJSONV1)
json_acq_invoice_search = search_responsify(_json, "application/rero+json")
json_acq_invoice_record = record_responsify(_json, "application/rero+json")
