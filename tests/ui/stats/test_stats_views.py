# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Stats views tests."""

from unittest import mock

from flask import url_for
from invenio_accounts.testutils import login_user_via_session

from tests.utils import parse_csv, parse_xlsx


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


def test_stats_librarian_query_exports(client, system_librarian_martigny):
    """Test CSV and XLSX exports for a librarian query."""
    login_user_via_session(client, system_librarian_martigny.user)
    query = "loans_of_transaction_library_by_item_location"
    record = mock.MagicMock()
    record.dumps.return_value = {
        "date_range": {
            "from": "2026-01-01T00:00:00",
            "to": "2026-01-31T23:59:59",
        },
        "values": [
            {
                "library": {"pid": "lib1", "name": "Library"},
                query: {
                    "lib1 - Main location": {
                        "location_name": "Main location",
                        "checkin": 2,
                        "checkout": 3,
                    }
                },
            }
        ],
    }

    with mock.patch(
        "rero_ils.modules.stats.views.Stat.get_record_by_pid",
        return_value=record,
    ):
        csv_url = url_for(
            "stats.stats_librarian_queries",
            record_pid="1",
            query_id=query,
        )
        csv_response = client.get(csv_url)
        assert csv_response.status_code == 200
        assert "/csv?" in csv_url

        xlsx_url = url_for(
            "stats.stats_librarian_queries_xlsx",
            record_pid="1",
            query_id=query,
        )
        xlsx_response = client.get(xlsx_url)
        assert xlsx_response.status_code == 200
        assert xlsx_response.mimetype == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert xlsx_response.headers["Content-Disposition"].endswith(".xlsx")
        assert xlsx_response.headers["X-Accel-Buffering"] == "no"
        assert parse_xlsx(xlsx_response.get_data()) == list(parse_csv(csv_response.get_data(as_text=True)))
