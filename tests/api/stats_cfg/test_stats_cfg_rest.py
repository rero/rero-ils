# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2023 RERO
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

"""Tests statistics configuration REST API."""

import mock
from flask import url_for
from utils import VerifyRecordPermissionPatch, get_json, to_relative_url


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_stats_cfg_get(client, stats_cfg_martigny):
    """Test record retrieval."""
    item_url = url_for(
        'invenio_records_rest.stacfg_item', pid_value=stats_cfg_martigny.pid)
    res = client.get(item_url)
    assert res.status_code == 200
    data = get_json(res)
    for k in ['created', 'updated', 'metadata', 'links']:
        assert k in data

    # Check self links
    res = client.get(to_relative_url(data['links']['self']))
    assert res.status_code == 200

    # search
    list_url = url_for('invenio_records_rest.stacfg_list')
    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['hits']
    assert data['aggregations']['category']['buckets']
