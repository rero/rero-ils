# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Patron transaction event serializers."""

from rero_ils.modules.serializers import RecordSchemaJSONV1, search_responsify

from .json import LocationJSONSerializer

__all__ = [
    "json_loc_search",
]


"""JSON serializer."""
_json = LocationJSONSerializer(RecordSchemaJSONV1)
json_loc_search = search_responsify(_json, "application/rero+json")
