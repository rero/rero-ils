# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests REST API loan deleted item."""

from flask.helpers import url_for
from invenio_accounts.testutils import login_user_via_session

from tests.utils import postdata


def test_loans_serializer_with_deleted_item(
    client,
    item_lib_martigny,
    patron2_martigny,
    librarian_martigny,
    lib_martigny,
    rero_json_header,
    circulation_policies,
):
    """Test loan serializer with a deleted item."""
    login_user_via_session(client, librarian_martigny.user)
    res, _ = postdata(
        client,
        "api_item.checkout",
        {
            "item_pid": item_lib_martigny.pid,
            "patron_pid": patron2_martigny.pid,
            "transaction_library_pid": lib_martigny.pid,
            "transaction_user_pid": librarian_martigny.pid,
        },
    )
    assert res.status_code == 200
    res, data = postdata(
        client,
        "api_item.checkin",
        {
            "item_pid": item_lib_martigny.pid,
            "transaction_library_pid": lib_martigny.pid,
            "transaction_user_pid": librarian_martigny.pid,
        },
    )
    assert res.status_code == 200

    item_lib_martigny.delete(False, True, True)

    loan_list_url = url_for("invenio_records_rest.loanid_list")
    res = client.get(loan_list_url, headers=rero_json_header)
    assert res.status_code == 200
