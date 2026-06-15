# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests REST API libraries."""

from flask import url_for
from invenio_accounts.testutils import login_user_via_session

from tests.utils import get_json


def test_library_closed_date_api(client, lib_martigny, librarian_martigny):
    """Test closed date api."""
    login_user_via_session(client, librarian_martigny.user)
    # CHECK#0 :: unknown library
    url = url_for("api_library.list_closed_dates", library_pid="dummy_pid")
    res = client.get(url)
    assert res.status_code == 404

    # CHECK#1 :: no specified dates
    url = url_for("api_library.list_closed_dates", library_pid=lib_martigny.pid)
    res = client.get(url)
    assert res.status_code == 200
    data = get_json(res)
    assert "closed_dates" in data
    assert isinstance(data["closed_dates"], list)

    # CHECK#2 :: with specified dates
    params = {"from": "2020-01-01", "until": "2020-02-01"}
    url = url_for("api_library.list_closed_dates", library_pid=lib_martigny.pid, **params)
    res = client.get(url)
    assert res.status_code == 200
    data = get_json(res)
    assert data["params"]["from"] == params["from"]
    assert data["params"]["until"] == params["until"]

    # CHECK#3 :: with bad specified dates
    params = {"until": "2020-01-01", "from": "2020-02-01"}
    url = url_for("api_library.list_closed_dates", library_pid=lib_martigny.pid, **params)
    res = client.get(url)
    assert res.status_code == 200
    data = get_json(res)
    assert data["params"]["from"] == params["from"]
    assert data["params"]["until"] == params["until"]
    assert data["closed_dates"] == []
