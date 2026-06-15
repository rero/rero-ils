# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test acquisition receipt API."""

from invenio_accounts.testutils import login_user_via_session

from rero_ils.modules.acquisition.acq_receipts.models import (
    AcqReceiptLineCreationStatus,
)
from tests.utils import get_json, postdata


def test_create_lines(
    app,
    client,
    librarian_martigny,
    lib_martigny,
    librarian_sion,
    acq_order_line_fiction_martigny,
    acq_order_line2_fiction_martigny,
    acq_receipt_fiction_martigny,
    json_header,
):
    """Test create_lines API."""
    login_user_via_session(client, librarian_martigny.user)
    receipt = acq_receipt_fiction_martigny
    receipt_lines = []
    # test when parent order is not in database
    res, data = postdata(
        client,
        "api_receipt.lines",
        data=receipt_lines,
        url_data={"receipt_pid": "toto"},
    )
    assert res.status_code == 404
    # test when receipt_lines data is not provided
    res, data = postdata(client, "api_receipt.lines", url_data={"receipt_pid": receipt.pid})
    assert res.status_code == 400
    # test when receipt_lines data provided but empty
    res, data = postdata(
        client,
        "api_receipt.lines",
        data=receipt_lines,
        url_data={"receipt_pid": receipt.pid},
    )
    assert res.status_code == 400
    # test when receipt_lines data provided
    receipt_lines = [
        {
            "acq_order_line": {"$ref": "https://bib.rero.ch/api/acq_order_lines/acol1"},
            "amount": 1000,
            "quantity": 1,
            "receipt_date": "2021-11-01",
        },
        {
            "acq_order_line": {"$ref": "https://bib.rero.ch/api/acq_order_lines/acol2"},
            "amount": 500,
            "quantity": 1,
            "receipt_date": "2021-11-03",
        },
        {"acq_order_line": {"$ref": "https://bib.rero.ch/api/acq_order_lines/acol2"}},
    ]

    res, data = postdata(
        client,
        "api_receipt.lines",
        data=receipt_lines,
        url_data={"receipt_pid": receipt.pid},
    )
    assert res.status_code == 200
    response = get_json(res).get("response")
    assert response[0]["status"] == AcqReceiptLineCreationStatus.SUCCESS
    assert response[1]["status"] == AcqReceiptLineCreationStatus.SUCCESS
    assert response[2]["status"] == AcqReceiptLineCreationStatus.FAILURE
    assert response[2]["error_message"]
