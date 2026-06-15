# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Acquisition budget serialization."""

from invenio_records_rest.serializers.response import record_responsify

from rero_ils.modules.serializers import ACQJSONSerializer, RecordSchemaJSONV1

_json = ACQJSONSerializer(RecordSchemaJSONV1)
json_budg_record = record_responsify(_json, "application/rero+json")
