# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Migration Record tests."""

from flask import url_for
from invenio_accounts.testutils import login_user_via_session


def test_migrations_rest(migration, client, patron_martigny, system_librarian_martigny, system_librarian_sion):
    """Test the migration REST API."""
    res = client.get(url_for("api_migrations.migrations_list"))
    assert res.status_code == 401

    login_user_via_session(client, patron_martigny.user)
    res = client.get(url_for("api_migrations.migrations_list"))
    assert res.status_code == 403

    login_user_via_session(client, system_librarian_martigny.user)
    res = client.get(url_for("api_migrations.migrations_list"))
    assert res.status_code == 200
    assert res.json["hits"]["total"]["value"] == 1
    assert res.json["hits"]["hits"][0]["id"] == migration.meta.id

    # transform datetime objects as strings
    data = migration.to_dict()
    data["updated_at"] = data["updated_at"].isoformat()
    data["created_at"] = data["created_at"].isoformat()
    assert res.json["hits"]["hits"][0]["metadata"] == data

    res = client.get(url_for("api_migrations.migrations_list", size=0))
    assert res.status_code == 200
    assert res.json["hits"]["total"]["value"] == 1
    assert res.json["hits"]["hits"] == []

    res = client.get(url_for("api_migrations.migrations_list", page=2, size=10))
    assert res.status_code == 200
    assert res.json["hits"]["total"]["value"] == 1
    assert res.json["hits"]["hits"] == []

    login_user_via_session(client, system_librarian_sion.user)
    res = client.get(url_for("api_migrations.migrations_list"))
    assert res.status_code == 200
    assert res.json["hits"]["total"]["value"] == 0
