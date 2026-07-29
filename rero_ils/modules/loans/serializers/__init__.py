# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""RERO-ILS Loan resource serializers."""

from rero_ils.modules.serializers import (
    RecordSchemaJSONV1,
    search_responsify,
    search_responsify_file,
)
from rero_ils.modules.serializers.utils import excel_xml_converter

from .csv import LoanStreamedCSVSerializer
from .json import LoanJSONSerializer

__all__ = ["csv_stream_search", "excel_xml_loan_search", "json_loan_search"]


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
excel_xml_loan_search = search_responsify_file(
    _streamed_csv,
    "application/vnd.ms-excel",
    file_extension="xls",
    file_prefix="export-loans",
    content_converter=excel_xml_converter(
        "rero_ils/exports/loans.xml",
        worksheet_name="Loans",
    ),
)
