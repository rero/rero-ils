# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""RERO ILS Record serialization."""

from invenio_records_rest.serializers.response import (
    record_responsify,
)
from invenio_records_rest.serializers.response import (
    search_responsify as _search_responsify,
)

from .base import ACQJSONSerializer, JSONSerializer
from .mixins import CachedDataSerializerMixin, StreamSerializerMixin
from .response import record_responsify_file, search_responsify, search_responsify_file
from .schema import RecordSchemaJSONV1

__all__ = [
    "ACQJSONSerializer",
    "CachedDataSerializerMixin",
    "JSONSerializer",
    "RecordSchemaJSONV1",
    "StreamSerializerMixin",
    "json_v1",
    "json_v1_response",
    "json_v1_search",
    "record_responsify_file",
    "search_responsify",
    "search_responsify_file",
]


json_v1 = JSONSerializer(RecordSchemaJSONV1)
json_v1_search = _search_responsify(json_v1, "application/json")
json_v1_response = record_responsify(json_v1, "application/json")
