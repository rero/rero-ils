# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Stats views tests."""

from unittest import mock

from flask import url_for
from invenio_accounts.testutils import login_user_via_session


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
