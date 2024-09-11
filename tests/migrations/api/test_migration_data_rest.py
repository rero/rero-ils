# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021-2023 RERO
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
    migration_data,
    client,
    patron_martigny,
    system_librarian_martigny,
    system_librarian_sion,
):
    """Test the migration REST API."""
    res = client.get(url_for("api_migration_data.migration_data_list"))
    assert res.status_code == 401

    login_user_via_session(client, patron_martigny.user)
    res = client.get(url_for("api_migration_data.migration_data_list"))
    assert res.status_code == 403

    login_user_via_session(client, system_librarian_martigny.user)
    res = client.get(url_for("api_migration_data.migration_data_list"))
    assert res.status_code == 200
    assert res.json["hits"]["total"]["value"] == 1
    assert res.json["hits"]["hits"][0]["id"] == migration_data.meta.id
    assert res.json["hits"]["hits"][0]["metadata"]
    assert res.json["aggregations"]

    res = client.get(
        url_for("api_migration_data.migration_data_list", conversion_status="invalid")
    )
    assert res.status_code == 200
    assert res.json["hits"]["total"]["value"] == 0

    res = client.get(
        url_for(
            "api_migration_data.migration_data_list",
            conversion_status="complete",
        )
    )
    assert res.status_code == 200
    assert res.json["hits"]["total"]["value"] == 1

    res = client.get(
        url_for(
            "api_migration_data.migration_data_list",
            migration=migration_data.migration_id,
        )
    )
    assert res.status_code == 200
    assert res.json["hits"]["total"]["value"] == 1

    res = client.get(url_for("api_migration_data.migration_data_list", size=0))
    assert res.status_code == 200
    assert res.json["hits"]["total"]["value"] == 1
    assert res.json["hits"]["hits"] == []

    res = client.get(url_for("api_migration_data.migration_data_list", page=2, size=10))
    assert res.status_code == 200
    assert res.json["hits"]["total"]["value"] == 1
    assert res.json["hits"]["hits"] == []

    login_user_via_session(client, system_librarian_sion.user)
    res = client.get(url_for("api_migration_data.migration_data_list"))
    assert res.status_code == 200
    assert res.json["hits"]["total"]["value"] == 0


def test_migrations_rest_get(
    migration,
    migration_data,
    client,
    patron_martigny,
    system_librarian_martigny,
    system_librarian_sion,
):
    """Test the migration REST API."""
    res = client.get(
        url_for(
            "api_migration_data.migration_data_item",
            migration=migration.meta.id,
            id=migration_data.meta.id,
        )
    )
    assert res.status_code == 401

    login_user_via_session(client, patron_martigny.user)
    res = client.get(
        url_for(
            "api_migration_data.migration_data_item",
            migration=migration.meta.id,
            id=migration_data.meta.id,
        )
    )
    assert res.status_code == 403

    login_user_via_session(client, system_librarian_martigny.user)
    res = client.get(
        url_for(
            "api_migration_data.migration_data_item",
            migration="invalid",
            id=migration_data.meta.id,
        )
    )
    assert res.status_code == 404

    res = client.get(
        url_for(
            "api_migration_data.migration_data_item",
            migration=migration.meta.id,
            id="invalid",
        )
    )
    assert res.status_code == 404

    res = client.get(
        url_for(
            "api_migration_data.migration_data_item",
            migration=migration.meta.id,
            id=migration_data.meta.id,
        )
    )
    assert res.status_code == 200
    data = migration_data.to_dict()
    data["raw"] = migration.conversion_class.markdown(migration_data.raw)
    data["id"] = migration_data.meta.id
    assert res.json == data
