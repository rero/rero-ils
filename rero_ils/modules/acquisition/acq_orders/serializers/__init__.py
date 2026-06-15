# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Acquisition order serialization."""

from invenio_records_rest.serializers.response import record_responsify

from rero_ils.modules.serializers import (
    RecordSchemaJSONV1,
    search_responsify,
    search_responsify_file,
)

from .csv import AcqOrderCSVSerializer
from .json import AcqOrderJSONSerializer

__all__ = ["csv_acor_search", "json_acor_record", "json_acor_search"]

"""JSON serializer."""
_json = AcqOrderJSONSerializer(RecordSchemaJSONV1)
json_acor_search = search_responsify(_json, "application/rero+json")
json_acor_record = record_responsify(_json, "application/rero+json")

"""CSV serializer."""
_csv = AcqOrderCSVSerializer(
    csv_included_fields=[
        "order_pid",
        "order_reference",
        "order_date",
        "order_staff_note",
        "order_vendor_note",
        "order_status",
        "vendor_name",
        "document_pid",
        "document_creator",
        "document_title",
        "document_publisher",
        "document_publication_year",
        "document_edition_statement",
        "document_series_statement",
        "document_isbn",
        "account_name",
        "account_number",
        "order_lines_priority",
        "order_lines_notes",
        "order_lines_status",
        "ordered_quantity",
        "ordered_unit_price",
        "ordered_amount",
        "receipt_reference",
        "received_quantity",
        "received_amount",
        "receipt_date",
    ]
)

csv_acor_search = search_responsify_file(_csv, "text/csv", file_extension="csv", file_prefix="export-orders")
