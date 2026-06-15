# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Patrons serialization."""

from rero_ils.modules.patron_types.api import PatronTypesSearch
from rero_ils.modules.serializers import (
    JSONSerializer,
    RecordSchemaJSONV1,
    search_responsify,
)


class PatronJSONSerializer(JSONSerializer):
    """Serializer for RERO-ILS `Patron` records as JSON."""

    def _postprocess_search_aggregations(self, aggregations):
        """Post-process aggregations from a search result."""
        JSONSerializer.enrich_bucket_with_data(
            aggregations.get("patron_type", {}).get("buckets", []),
            PatronTypesSearch,
            "name",
        )
        super()._postprocess_search_aggregations(aggregations)


_json = PatronJSONSerializer(RecordSchemaJSONV1)
json_patron_search = search_responsify(_json, "application/rero+json")
