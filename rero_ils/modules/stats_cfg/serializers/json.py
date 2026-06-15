# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Statistics configuration serialization."""

from rero_ils.modules.libraries.api import LibrariesSearch
from rero_ils.modules.serializers import JSONSerializer
from rero_ils.modules.serializers.mixins import PostprocessorMixin


class StatsCfgJSONSerializer(JSONSerializer, PostprocessorMixin):
    """Mixin serializing records as JSON."""

    def _postprocess_search_aggregations(self, aggregations):
        """Post-process aggregations from a search result.

        :param aggregations: the dictionary representing ElasticSearch
                            aggregations section.
        """
        JSONSerializer.enrich_bucket_with_data(
            aggregations.get("library", {}).get("buckets", []), LibrariesSearch, "name"
        )

        super()._postprocess_search_aggregations(aggregations)
