# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests UI view for collections."""

from flask import url_for


def test_collection_detailed_view(client, coll_martigny_1):
    """Test collection detailed view."""
    # check redirection
    res = client.get(url_for("invenio_records_ui.coll", viewcode="org1", pid_value=coll_martigny_1.pid))
    assert res.status_code == 200
