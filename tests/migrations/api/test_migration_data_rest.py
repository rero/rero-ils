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

import json

from flask import jsonify, url_for
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
    res = client.get(
        url_for("api_migration_data.migration_data_list", sort="-updated_at")
    )
    assert res.status_code == 200
    assert res.json["hits"]["total"]["value"] == 1
    assert res.json["hits"]["hits"][0]["id"] == migration_data.meta.id
    assert res.json["hits"]["hits"][0]["metadata"]
    aggs = res.json["aggregations"]
    assert set(aggs.keys()) == {
        "batch",
        "conversion_status",
        "deduplication_status",
        "migration",
        "modified_by",
    }
    args = {}
    for agg in [
        "batch",
        "conversion_status",
        "deduplication_status",
        "migration",
        "modified_by",
    ]:
        assert aggs[agg]["buckets"][0]["doc_count"] == 1
        key = aggs[agg]["buckets"][0]["key"]
        args[agg] = key
    res = client.get(url_for("api_migration_data.migration_data_list", **args))
    assert res.status_code == 200
    assert res.json["hits"]["total"]["value"] == 1

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

    res = client.get(
        url_for(
            "api_migration_data.migration_data_list",
            migration="invalid",
        )
    )
    assert res.status_code == 404

    res = client.get(
        url_for(
            "api_migration_data.migration_data_list",
            migration=migration_data.migration_id,
            q="should not exists",
        )
    )
    assert res.status_code == 200
    assert res.json["hits"]["total"]["value"] == 0

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
            migration="invalid",
            id=migration_data.meta.id,
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
    assert res.json == jsonify(data).json


def test_migrations_rest_put(
    migration,
    migration_data,
    client,
    patron_martigny,
    system_librarian_martigny,
    system_librarian_sion,
    json_header,
    document,
):
    """Test the migration REST API."""
    login_user_via_session(client, system_librarian_martigny.user)
    res = client.put(
        url_for(
            "api_migration_data.migration_data_item",
            migration=migration.meta.id,
            id="invalid",
        ),
        data=json.dumps({"ils_pid": None}),
        headers=json_header,
    )
    assert res.status_code == 404

    res = client.put(
        url_for(
            "api_migration_data.migration_data_item",
            migration="invalid",
            id=migration_data.meta.id,
        ),
        data=json.dumps({"ils_pid": None}),
        headers=json_header,
    )
    assert res.status_code == 404

    res = client.put(
        url_for(
            "api_migration_data.migration_data_item",
            migration=migration.meta.id,
            id=migration_data.meta.id,
        ),
        data=json.dumps({"ils_pid": None}),
        headers=json_header,
    )
    assert res.status_code == 200
    assert res.json["deduplication"]["status"] == "no match"

    res = client.put(
        url_for(
            "api_migration_data.migration_data_item",
            migration=migration.meta.id,
            id=migration_data.meta.id,
        ),
        data=json.dumps(
            {
                "ils_pid": document.pid,
                "candidates": [{"json": document.dumps(), "pid": document.pid}],
            }
        ),
        headers=json_header,
    )
    assert res.status_code == 200
    assert res.json["deduplication"]["status"] == "match"
    assert (
        res.json["deduplication"]["modified_by"]
        == system_librarian_martigny.formatted_name
    )
    assert res.json["deduplication"]["modified_by"]
