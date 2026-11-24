# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Test REST API monitoring."""

import pytest
from flask import current_app, url_for
from flask_security.utils import hash_password
from invenio_accounts.testutils import login_user_via_session

from rero_ils.modules.entities.remote_entities.api import (
    RemoteEntitiesSearch,
    RemoteEntity,
)
from tests.utils import get_json


@pytest.fixture()
def monitoring_user(app, db, default_user_password):
    """Create a user with the monitoring role."""
    ds = app.extensions["invenio-accounts"].datastore
    user = ds.create_user(
        email="monitoring@rero.ch",
        password=hash_password(default_user_password),
        active=True,
    )
    role = ds.create_role(name="monitoring", description="Monitoring Group")
    ds.add_role_to_user(user, role)
    ds.commit()
    return ds.get_user("monitoring@rero.ch")


def test_monitoring_search_db_counts(client, monitoring_user):
    """Every record type is counted, the ones without database records in the index only."""
    login_user_via_session(client, monitoring_user)
    res = client.get(url_for("api_monitoring.search_db_counts"))
    assert res.status_code == 200
    assert get_json(res) == {
        "data": {
            "acac": {"db": 0, "db-search": 0, "search": 0, "index": "acq_accounts"},
            "acol": {"db": 0, "db-search": 0, "search": 0, "index": "acq_order_lines"},
            "acor": {"db": 0, "db-search": 0, "search": 0, "index": "acq_orders"},
            "acre": {"db": 0, "db-search": 0, "search": 0, "index": "acq_receipts"},
            "acrl": {"db": 0, "db-search": 0, "search": 0, "index": "acq_receipt_lines"},
            "budg": {"db": 0, "db-search": 0, "search": 0, "index": "budgets"},
            "cipo": {"db": 0, "db-search": 0, "search": 0, "index": "circ_policies"},
            "coll": {"db": 0, "db-search": 0, "search": 0, "index": "collections"},
            "rement": {"db": 0, "db-search": 0, "search": 0, "index": "remote_entities"},
            "doc": {"db": 0, "db-search": 0, "search": 0, "index": "documents"},
            "hold": {"db": 0, "db-search": 0, "search": 0, "index": "holdings"},
            "illr": {"db": 0, "db-search": 0, "search": 0, "index": "ill_requests"},
            "item": {"db": 0, "db-search": 0, "search": 0, "index": "items"},
            "itty": {"db": 0, "db-search": 0, "search": 0, "index": "item_types"},
            "lib": {"db": 0, "db-search": 0, "search": 0, "index": "libraries"},
            "loanid": {"db": 0, "db-search": 0, "search": 0, "index": "loans"},
            "loc": {"db": 0, "db-search": 0, "search": 0, "index": "locations"},
            "locent": {"db": 0, "db-search": 0, "search": 0, "index": "local_entities"},
            "lofi": {"db": 0, "db-search": 0, "search": 0, "index": "local_fields"},
            "notif": {"db": 0, "db-search": 0, "search": 0, "index": "notifications"},
            "oplg": {"db": 0, "db-search": 0, "search": 0, "index": "operation_logs"},
            "org": {"db": 0, "db-search": 0, "search": 0, "index": "organisations"},
            "ptre": {
                "db": 0,
                "db-search": 0,
                "search": 0,
                "index": "patron_transaction_events",
            },
            "ptrn": {"db": 0, "db-search": 0, "search": 0, "index": "patrons"},
            "pttr": {"db": 0, "db-search": 0, "search": 0, "index": "patron_transactions"},
            "ptty": {"db": 0, "db-search": 0, "search": 0, "index": "patron_types"},
            "stacfg": {"db": 0, "db-search": 0, "search": 0, "index": "stats_cfg"},
            "stat": {"db": 0, "db-search": 0, "search": 0, "index": "stats"},
            "tmpl": {"db": 0, "db-search": 0, "search": 0, "index": "templates"},
            "ent": {"db": 0, "db-search": 0, "search": 0, "index": "entities"},
            "vndr": {"db": 0, "db-search": 0, "search": 0, "index": "vendors"},
        }
    }


def test_monitoring_check_search_db_counts(client, entity_person_data, monitoring_user):
    """The records missing in the index are linked to their REST endpoint."""
    login_user_via_session(client, monitoring_user)
    res = client.get(url_for("api_monitoring.check_search_db_counts", delay=0))
    assert res.status_code == 200
    assert get_json(res) == {"data": {"status": "green"}}

    RemoteEntity.create(data=entity_person_data, delete_pid=False, dbcommit=True, reindex=False)
    RemoteEntitiesSearch.flush_and_refresh()
    res = client.get(url_for("api_monitoring.check_search_db_counts", delay=0))
    assert res.status_code == 200
    assert get_json(res) == {
        "data": {"status": "red"},
        "errors": [
            {
                "code": "DB_SEARCH_COUNTER_MISMATCH",
                "details": "There are 1 items from rement missing in search.",
                "id": "DB_SEARCH_COUNTER_MISMATCH",
                "links": {
                    "about": "http://localhost/monitoring/check_search_db_counts?delay=0",
                    "rement": "http://localhost/monitoring/missing_pids/rement?delay=0",
                },
                "title": "DB items counts don't match search items count.",
            }
        ],
    }

    res = client.get(url_for("api_monitoring.missing_pids", doc_type="rement", delay=0))
    assert res.status_code == 200
    assert get_json(res) == {
        "data": {
            "DB": [],
            "search": ["http://localhost/remote_entities/ent_pers"],
            "search duplicate": [],
        }
    }


def test_monitoring_redis(client, monitoring_user):
    """Every configured Redis instance is described."""
    login_user_via_session(client, monitoring_user)
    res = client.get(url_for("api_monitoring.redis"))
    assert res.status_code == 200
    data = get_json(res)["data"]
    expected = {
        name
        for name, config_key in current_app.config["RERO_INVENIO_BASE_MONITORING_REDIS"].items()
        if str(current_app.config.get(config_key)).startswith(("redis://", "rediss://", "unix://"))
    }
    assert expected
    assert set(data.keys()) == expected
    assert all("redis_version" in info for info in data.values())
    assert all(info["name"] == name for name, info in data.items())
