# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

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
        url_data=dict(receipt_pid="toto"),
    )
    assert res.status_code == 404
    # test when receipt_lines data is not provided
    res, data = postdata(
        client, "api_receipt.lines", url_data=dict(receipt_pid=receipt.pid)
    )
    assert res.status_code == 400
    # test when receipt_lines data provided but empty
    res, data = postdata(
        client,
        "api_receipt.lines",
        data=receipt_lines,
        url_data=dict(receipt_pid=receipt.pid),
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
        url_data=dict(receipt_pid=receipt.pid),
    )
    assert res.status_code == 200
    response = get_json(res).get("response")
    assert response[0]["status"] == AcqReceiptLineCreationStatus.SUCCESS
    assert response[1]["status"] == AcqReceiptLineCreationStatus.SUCCESS
    assert response[2]["status"] == AcqReceiptLineCreationStatus.FAILURE
    assert response[2]["error_message"]
