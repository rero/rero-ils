# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Stats views tests."""

from unittest import mock

from flask import url_for
from invenio_accounts.testutils import login_user_via_session

from tests.utils import assert_xlsx_response, get_csv, parse_csv


def test_view_status(client, patron_martigny, librarian_martigny, system_librarian_martigny):
    """Test view status."""
    # User not logged
    result = client.get(url_for("stats.stats_billing"))
    assert result.status_code == 401

    # User without access permissions
    login_user_via_session(client, patron_martigny.user)
    result = client.get(url_for("stats.stats_billing"))
    assert result.status_code == 403

    result = client.get(url_for("stats.live_stats_billing"))
    assert result.status_code == 403

    # User with librarian permissions
    login_user_via_session(client, librarian_martigny.user)
    result = client.get(url_for("stats.stats_billing"))
    assert result.status_code == 403

    result = client.get(url_for("stats.live_stats_billing"))
    assert result.status_code == 403

    result = client.get(url_for("stats.stats_librarian"))
    assert result.status_code == 403

    result = client.get(url_for("stats.stats_librarian", record_pid=1))
    assert result.status_code == 403

    # User with system librarian permissions
    login_user_via_session(client, system_librarian_martigny.user)
    result = client.get(url_for("stats.stats_billing"))
    assert result.status_code == 403

    result = client.get(url_for("stats.live_stats_billing"))
    assert result.status_code == 403

    result = client.get(url_for("stats.stats_librarian"))
    assert result.status_code == 200

    result = client.get(url_for("stats.stats_librarian", record_pid=1))
    assert result.status_code == 200

    with mock.patch("rero_ils.modules.stats.permissions.admin_permission", mock.MagicMock()):
        result = client.get(url_for("stats.stats_billing"))
        assert result.status_code == 200


def test_stats_librarian_query_xlsx(client, stats_librarian, system_librarian_martigny):
    """Test a librarian statistics query exported as XLSX."""
    login_user_via_session(client, system_librarian_martigny.user)
    url = url_for(
        "stats.stats_librarian_queries",
        record_pid=stats_librarian.pid,
        file_format="xlsx",
        query_id="loans_of_transaction_library_by_item_location",
    )
    xlsx_rows = assert_xlsx_response(client.get(url))
    csv_url = url_for(
        "stats.stats_librarian_queries",
        record_pid=stats_librarian.pid,
        file_format="csv",
        query_id="loans_of_transaction_library_by_item_location",
    )
    csv_rows = list(parse_csv(get_csv(client.get(csv_url))))
    assert xlsx_rows[0] == csv_rows[0]
    assert xlsx_rows[1][0] == csv_rows[1][0]


def test_stats_librarian_query_legacy_csv(client, stats_librarian, system_librarian_martigny):
    """Test the legacy librarian statistics CSV URL."""
    login_user_via_session(client, system_librarian_martigny.user)
    response = client.get(
        f"/stats/librarian/{stats_librarian.pid}/csv",
        query_string={"query_id": "loans_of_transaction_library_by_item_location"},
    )

    assert response.status_code == 200
    assert response.mimetype == "text/csv"
    assert response.headers["Content-Disposition"].endswith(".csv")
