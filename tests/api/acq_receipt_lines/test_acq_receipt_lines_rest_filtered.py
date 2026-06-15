# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests REST API acquisition receipt lines."""

from flask import url_for
from invenio_accounts.testutils import login_user_via_session

from tests.utils import get_json


def test_filtered_acq_receipt_lines_get(
    client,
    librarian_martigny,
    acq_order_line_fiction_martigny,
    acq_order_line2_fiction_martigny,
    acq_receipt_line_1_fiction_martigny,
    acq_receipt_line_2_fiction_martigny,
    librarian_sion,
    acq_receipt_line_fiction_sion,
):
    """Test acq receipt lines filter by organisation."""
    list_url = url_for("invenio_records_rest.acrl_list")

    res = client.get(list_url)
    assert res.status_code == 401

    # Martigny
    login_user_via_session(client, librarian_martigny.user)
    list_url = url_for("invenio_records_rest.acrl_list")

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data["hits"]["total"]["value"] == 2

    # Sion
    login_user_via_session(client, librarian_sion.user)
    list_url = url_for("invenio_records_rest.acrl_list")

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data["hits"]["total"]["value"] == 1
