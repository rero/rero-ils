# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""ILL Request serialization."""

from flask_babel import gettext as _
from invenio_records_rest.serializers.response import record_responsify

from rero_ils.modules.libraries.api import LibrariesSearch
from rero_ils.modules.locations.api import LocationsSearch
from rero_ils.modules.serializers import (
    CachedDataSerializerMixin,
    JSONSerializer,
    RecordSchemaJSONV1,
    search_responsify,
)


class ILLRequestJSONSerializer(JSONSerializer, CachedDataSerializerMixin):
    """Serializer for RERO-ILS `ILLRequest` records as JSON."""

    def _postprocess_search_hit(self, hit):
        """Post-process each hit of a search result."""
        pickup_location = hit.get("metadata", {}).setdefault("pickup_location", {})
        pickup_location["name"] = _("Unknown")
        if (pid := pickup_location.get("pid")) and (location := self.get_resource(LocationsSearch(), pid)):
            pickup_location["name"] = location.get("ill_pickup_name") or location.get("name") or pickup_location["name"]
        super()._postprocess_search_hit(hit)

    def _postprocess_search_aggregations(self, aggregations):
        """Post-process aggregations from a search result."""
        JSONSerializer.enrich_bucket_with_data(
            aggregations.get("library", {}).get("buckets", []), LibrariesSearch, "name"
        )
        super()._postprocess_search_aggregations(aggregations)


_json = ILLRequestJSONSerializer(RecordSchemaJSONV1)
json_ill_request_search = search_responsify(_json, "application/rero+json")
json_ill_request_response = record_responsify(_json, "application/rero+json")
