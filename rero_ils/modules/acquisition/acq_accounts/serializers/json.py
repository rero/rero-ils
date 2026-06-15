# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Acquisition account serialization."""

from rero_ils.modules.libraries.api import LibrariesSearch
from rero_ils.modules.serializers import ACQJSONSerializer, JSONSerializer

from ..api import AcqAccountsSearch


class AcqAccountJSONSerializer(ACQJSONSerializer):
    """Serializer for RERO-ILS `AcqAccount` records as JSON."""

    def _postprocess_search_hit(self, hit):
        """Post-process each hit of a search result."""
        hit["metadata"]["number_of_children"] = (
            AcqAccountsSearch().filter("term", parent__pid=hit["metadata"]["pid"]).count()
        )
        super()._postprocess_search_hit(hit)

    def preprocess_record(self, pid, record, links_factory=None, **kwargs):
        """Prepare a record and persistent identifier for serialization."""
        # Add some search stored keys into response
        query = AcqAccountsSearch().filter("term", pid=record.pid).source()
        if hit := next(query.scan(), None):
            hit_metadata = hit.to_dict()
            keys = [
                "depth",
                "distribution",
                "is_active",
                "encumbrance_exceedance",
                "expenditure_exceedance",
                "encumbrance_amount",
                "expenditure_amount",
                "remaining_balance",
            ]
            for key in keys:
                value = hit_metadata.get(key)
                if value is not None:
                    record[key] = value

        return super().preprocess_record(pid=pid, record=record, links_factory=links_factory, kwargs=kwargs)

    def _postprocess_search_aggregations(self, aggregations):
        """Post-process aggregations from a search result."""
        JSONSerializer.enrich_bucket_with_data(
            aggregations.get("library", {}).get("buckets", []), LibrariesSearch, "name"
        )
        super()._postprocess_search_aggregations(aggregations)
