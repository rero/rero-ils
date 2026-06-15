# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests statistics configuration REST API."""

from unittest import mock

from flask import url_for

from tests.utils import VerifyRecordPermissionPatch, get_json, to_relative_url


@mock.patch(
    "invenio_records_rest.views.verify_record_permission",
    mock.MagicMock(return_value=VerifyRecordPermissionPatch),
)
def test_stats_cfg_get(client, stats_cfg_martigny):
    """Test record retrieval."""
    item_url = url_for("invenio_records_rest.stacfg_item", pid_value=stats_cfg_martigny.pid)
    res = client.get(item_url)
    assert res.status_code == 200
    data = get_json(res)
    for k in ["created", "updated", "metadata", "links"]:
        assert k in data

    # Check self links
    res = client.get(to_relative_url(data["links"]["self"]))
    assert res.status_code == 200

    # search
    list_url = url_for("invenio_records_rest.stacfg_list")
    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data["hits"]["hits"]
    assert data["aggregations"]["category"]["buckets"]
