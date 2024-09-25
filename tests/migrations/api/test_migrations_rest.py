# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021-2024 RERO
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

"""Migration Record tests."""

from flask import url_for
from invenio_accounts.testutils import login_user_via_session


def test_migrations_rest(
    migration, client, patron_martigny, system_librarian_martigny, system_librarian_sion
):
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
