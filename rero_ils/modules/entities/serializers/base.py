# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""RERO Entity JSON serialization."""

from rero_ils.modules.serializers import JSONSerializer


class EntityJSONSerializer(JSONSerializer):
    """Serializer for RERO-ILS `Document` records as JSON."""

    def _postprocess_search_links(self, search_results, pid_fetcher):
        """Post-process search links.

        :param search_results: search index search result.
        :param pid_fetcher: Persistent identifier fetcher related to records
                            into the search result.
        """
        # DEV NOTES :
        # We need to override this method to remove the `create` link from
        # search results.
        # See `rero_ils.modules.serializers.mixins.PostprocessorMixin`
