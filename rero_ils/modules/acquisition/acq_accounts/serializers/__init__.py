# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Acquisition accounts serialization."""

from invenio_records_rest.serializers.response import record_responsify

from rero_ils.modules.serializers import (
    RecordSchemaJSONV1,
    search_responsify,
    search_responsify_file,
)

from .csv import AcqAccountCSVSerializer
from .json import AcqAccountJSONSerializer

__all__ = [
    "csv_acq_account_search",
    "json_acq_account_response",
    "json_acq_account_search",
]

"""JSON v1 serializer."""
_json = AcqAccountJSONSerializer(RecordSchemaJSONV1)
json_acq_account_search = search_responsify(_json, "application/rero+json")
json_acq_account_response = record_responsify(_json, "application/rero+json")

"""CSV serializer."""
_csv = AcqAccountCSVSerializer(
    csv_included_fields=[
        "account_pid",
        "account_name",
        "account_number",
        "account_allocated_amount",
        "account_available_amount",
        "account_current_encumbrance",
        "account_current_expenditure",
        "account_available_balance",
    ]
)

csv_acq_account_search = search_responsify_file(_csv, "text/csv", file_extension="csv", file_prefix="export-accounts")
