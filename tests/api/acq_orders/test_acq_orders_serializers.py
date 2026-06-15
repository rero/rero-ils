# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests Serializers."""

from flask import url_for
from invenio_accounts.testutils import login_user_via_session

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
