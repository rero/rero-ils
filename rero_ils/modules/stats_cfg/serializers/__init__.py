# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Stat configuration serialization."""

from rero_ils.modules.serializers import RecordSchemaJSONV1, search_responsify

from .json import StatsCfgJSONSerializer

__all__ = ["json_search"]

"""JSON serializer."""
_json = StatsCfgJSONSerializer(RecordSchemaJSONV1)
json_search = search_responsify(_json, "application/rero+json")
