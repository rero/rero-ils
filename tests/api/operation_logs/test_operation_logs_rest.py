# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
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

"""Tests REST API operation logs."""

from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import get_json, postdata


def test_operation_logs_permissions(client, operation_log, patron_sion,
                                    librarian_martigny, json_header):
    """Test operation logs permissions."""
    item_url = url_for('invenio_records_rest.oplg_item', pid_value='1')
    item_list = url_for('invenio_records_rest.oplg_list')

    res = client.get(item_url)
    assert res.status_code == 404

    res = client.get(item_list)
    assert res.status_code == 401

    res, _ = postdata(
        client,
        'invenio_records_rest.oplg_list',
        {}
    )
    assert res.status_code == 401

    res = client.put(
        url_for('invenio_records_rest.oplg_item', pid_value='1'),
        data={},
        headers=json_header
    )
    assert res.status_code == 404

    res = client.delete(item_url)
    assert res.status_code == 404


def test_operation_logs_rest(client, loan_pending_martigny,
                             librarian_martigny,
                             json_header,
                             loan_overdue_martigny):
    """Test operation logs REST API."""
    login_user_via_session(client, librarian_martigny.user)
    item_url = url_for('invenio_records_rest.oplg_item', pid_value='1')
    item_list = url_for('invenio_records_rest.oplg_list')

    res = client.get(item_url)
    assert res.status_code == 404

    res = client.get(item_list)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total']['value'] > 0
    pid = data['hits']['hits'][0]['metadata']['pid']
    assert pid
    assert data['hits']['hits'][0]['id'] == pid
    assert data['hits']['hits'][0]['created']
    assert data['hits']['hits'][0]['updated']

    res, _ = postdata(
        client,
        'invenio_records_rest.oplg_list',
        {}
    )
    assert res.status_code == 403

    res = client.put(
        url_for('invenio_records_rest.oplg_item', pid_value='1'),
        data={},
        headers=json_header
    )
    assert res.status_code == 404

    res = client.delete(item_url)
    assert res.status_code == 404
