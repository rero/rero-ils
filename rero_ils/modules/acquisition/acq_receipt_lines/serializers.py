# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Acquisition receipt line serialization."""

from invenio_records_rest.serializers.response import record_responsify

from rero_ils.modules.serializers import (
    ACQJSONSerializer,
    RecordSchemaJSONV1,
    search_responsify,
)

_json = ACQJSONSerializer(RecordSchemaJSONV1)
json_acrl_search = search_responsify(_json, "application/rero+json")
json_acrl_record = record_responsify(_json, "application/rero+json")
