# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Location serialization."""

from rero_ils.modules.libraries.api import LibrariesSearch
from rero_ils.modules.serializers import CachedDataSerializerMixin, JSONSerializer


class LocationJSONSerializer(JSONSerializer, CachedDataSerializerMixin):
    """Serializer for RERO-ILS `Location` records as JSON."""

    def _postprocess_search_hit(self, hit):
        """Post-process each hit of a search result."""
        metadata = hit.get("metadata", {})

        # Add label for some $ref fields.
        pid = metadata.get("library", {}).get("pid")
        if pid and (resource := self.get_resource(LibrariesSearch(), pid)):
            metadata["library"]["code"] = resource.get("code")
            metadata["library"]["name"] = resource.get("name")
        super()._postprocess_search_hit(hit)
