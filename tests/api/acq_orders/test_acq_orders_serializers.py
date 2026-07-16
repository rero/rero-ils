# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests Serializers."""

import csv
from io import StringIO

from flask import url_for
from invenio_accounts.testutils import login_user_via_session

from rero_ils.modules.documents.api import DocumentsSearch
from tests.utils import get_csv


def test_csv_serializer(
    client,
    csv_header,
    librarian_martigny,
    acq_account_fiction_martigny,
    vendor_martigny,
    acq_order_fiction_martigny,
    acq_order_line_fiction_martigny,
    acq_order_line2_fiction_martigny,
    acq_receipt_fiction_martigny,
    acq_receipt_line_1_fiction_martigny,
    acq_receipt_line_2_fiction_martigny,
):
    """Test CSV formatter"""
    login_user_via_session(client, librarian_martigny.user)
    list_url = url_for("api_exports.acq_order_export", q=f"pid:{acq_order_fiction_martigny.pid}")
    response = client.get(list_url, headers=csv_header)
    assert response.status_code == 200
    data = get_csv(response)
    assert data
    assert (
        '"order_pid","order_reference","order_date","order_staff_note",'
        '"order_vendor_note","order_status","vendor_name",'
        '"document_pid","document_creator","document_title",'
        '"document_publisher","document_publication_year",'
        '"document_edition_statement","document_series_statement",'
        '"document_isbn","account_name","account_number",'
        '"order_lines_priority","order_lines_notes","order_lines_status",'
        '"ordered_quantity","ordered_unit_price","ordered_amount",'
        '"receipt_reference","received_quantity","received_amount",'
        '"receipt_date"' in data
    )


def test_csv_serializer_missing_document(
    client,
    csv_header,
    librarian_martigny,
    acq_account_fiction_martigny,
    vendor_martigny,
    acq_order_fiction_martigny,
    acq_order_line_fiction_martigny,
    acq_order_line2_fiction_martigny,
    document,
):
    """Test CSV export keeps streaming when a linked document is missing.

    A document may be deleted from the search index while still referenced by
    a terminal order line. The export must export every order line instead of
    crashing the stream, and display a placeholder for the missing document.
    """
    login_user_via_session(client, librarian_martigny.user)
    order = acq_order_fiction_martigny

    # Remove the document from the search index.
    document.delete_from_index()
    DocumentsSearch.flush_and_refresh()

    try:
        list_url = url_for("api_exports.acq_order_export", q=f"pid:{order.pid}")
        response = client.get(list_url, headers=csv_header)
        assert response.status_code == 200
        rows = list(csv.DictReader(StringIO(get_csv(response))))
    finally:
        # Restore the shared module-scoped fixture for the other tests.
        document.reindex()
        DocumentsSearch.flush_and_refresh()

    # Both order lines are still exported: the stream was not truncated.
    order_rows = [row for row in rows if row["order_pid"] == order.pid]
    assert len(order_rows) >= 2
    for row in order_rows:
        assert row["document_pid"] == document.pid
        assert row["document_title"] == "unknown"
