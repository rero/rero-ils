# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""RERO Unified entities serialization."""

from rero_ils.modules.serializers import RecordSchemaJSONV1, search_responsify

from .base import EntityJSONSerializer

# Serializers
# ===========
_json = EntityJSONSerializer(RecordSchemaJSONV1)

# Records-REST serializers
# ========================
json_entities_search = search_responsify(_json, "application/json")
