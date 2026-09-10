# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""RERO-ILS Loan resource serializers."""

from rero_invenio_base.modules.export import xlsx_converter

from rero_ils.modules.serializers import (
    RecordSchemaJSONV1,
    search_responsify,
    search_responsify_file,
)

from .base import requests_to_validate_rows
from .csv import LoanStreamedCSVSerializer, RequestsToValidateCSVSerializer
from .json import LoanJSONSerializer, RequestsToValidateJSONSerializer

__all__ = [
    "csv_requests_search",
    "csv_stream_search",
    "json_loan_search",
    "json_requests_search",
    "requests_to_validate_rows",
    "xlsx_loan_search",
    "xlsx_requests_search",
]


_json = LoanJSONSerializer(RecordSchemaJSONV1)
_streamed_csv = LoanStreamedCSVSerializer(
    csv_included_fields=[
        "pid",
        "document_title",
        "item_barcode",
        "item_call_numbers",
        "patron_name",
        "patron_barcode",
        "patron_email",
        "patron_type",
        "owning_library",
        "transaction_library",
        "pickup_library",
        "state",
        "checkout_date",
        "end_date",
        "request_expire_date",
    ]
)

json_loan_search = search_responsify(_json, "application/rero+json")
csv_stream_search = search_responsify_file(_streamed_csv, "text/csv", file_extension="csv", file_prefix="export-loans")
xlsx_loan_search = search_responsify_file(
    _streamed_csv,
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    file_extension="xlsx",
    file_prefix="export-loans",
    content_converter=xlsx_converter(
        "rero_ils/exports/loans.xml",
        worksheet_name="Loans",
    ),
)

_requests_csv = RequestsToValidateCSVSerializer(
    csv_included_fields=[
        "item_barcode",
        "document_title",
        "document_contributions",
        "item_first_call_number",
        "item_second_call_number",
        "item_enumerationAndChronology",
        "requested_by",
        "item_location",
        "pickup_location",
        "request_date",
    ]
)
_requests_json = RequestsToValidateJSONSerializer()

json_requests_search = search_responsify_file(
    _requests_json, "application/json", file_extension="json", file_prefix="export-requests"
)
csv_requests_search = search_responsify_file(
    _requests_csv, "text/csv", file_extension="csv", file_prefix="export-requests"
)
xlsx_requests_search = search_responsify_file(
    _requests_csv,
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    file_extension="xlsx",
    file_prefix="export-requests",
    content_converter=xlsx_converter(
        "rero_ils/exports/requests.xml",
        worksheet_name="Requests",
    ),
)
