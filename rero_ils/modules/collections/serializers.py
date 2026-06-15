# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Collection serialization."""

from rero_ils.modules.libraries.api import LibrariesSearch
from rero_ils.modules.serializers import (
    JSONSerializer,
    RecordSchemaJSONV1,
    search_responsify,
)


class CollectionJSONSerializer(JSONSerializer):
    """Serializer for RERO-ILS `Collection` records as JSON."""

    def _postprocess_search_aggregations(self, aggregations):
        """Post-process aggregations from a search result."""
        JSONSerializer.enrich_bucket_with_data(
            aggregations.get("library", {}).get("buckets", []), LibrariesSearch, "name"
        )
        super()._postprocess_search_aggregations(aggregations)


_json = CollectionJSONSerializer(RecordSchemaJSONV1)
json_coll_search = search_responsify(_json, "application/rero+json")
