# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Patron transaction event serializers."""

from rero_ils.modules.serializers import (
    RecordSchemaJSONV1,
    search_responsify,
    search_responsify_file,
)
from rero_ils.modules.serializers.utils import csv_to_xlsx

from .csv import PatronTransactionEventCSVSerializer
from .json import PatronTransactionEventsJSONSerializer

__all__ = ["csv_ptre_search", "json_ptre_search", "xlsx_ptre_search"]


"""JSON serializer."""
_json = PatronTransactionEventsJSONSerializer(RecordSchemaJSONV1)
json_ptre_search = search_responsify(_json, "application/rero+json")

"""CSV serializer."""
_csv = PatronTransactionEventCSVSerializer(
    csv_included_fields=[
        "category",
        "type",
        "subtype",
        "transaction_date",
        "amount",
        "patron_name",
        "patron_barcode",
        "patron_email",
        "patron_type",
        "document_pid",
        "document_title",
        "item_barcode",
        "item_owning_library",
        "transaction_library",
        "operator_name",
    ]
)

csv_ptre_search = search_responsify_file(_csv, "text/csv", file_extension="csv", file_prefix="export-fees")
xlsx_ptre_search = search_responsify_file(
    _csv,
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    file_extension="xlsx",
    file_prefix="export-fees",
    content_converter=csv_to_xlsx,
)
