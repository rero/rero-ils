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
from copy import deepcopy
from datetime import datetime

import mock
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import VerifyRecordPermissionPatch, flush_index, get_json, postdata

from rero_ils.modules.items.api import Item
from rero_ils.modules.items.models import ItemStatus
from rero_ils.modules.operation_logs.api import OperationLog
from rero_ils.modules.operation_logs.models import OperationLogOperation


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_operation_logs_permissions(client, operation_log,
                                    librarian_martigny, patron_martigny,
                                    librarian_patron_martigny, json_header):
    """Test operation logs permissions."""
    item_list = url_for('invenio_records_rest.oplg_list')

    # Check access for librarian role
    login_user_via_session(client, librarian_martigny.user)
    res = client.get(item_list)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total']['value'] == 4

    # Check access for patron role
    login_user_via_session(client, patron_martigny.user)
    res = client.get(item_list)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total']['value'] == 0

    # Check access for patron and librarian roles
    login_user_via_session(client, librarian_patron_martigny.user)
    res = client.get(item_list)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total']['value'] == 4


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


def test_operation_log_on_item(
    client, item_lib_martigny_data_tmp, librarian_martigny, json_header,
    item_lib_martigny
):
    """Test operation log on Item."""

    # Get the operation log index
    fake_data = {'date': datetime.now().isoformat()}
    oplg_index = OperationLog.get_index(fake_data)

    # STEP #1 : Create an item. This will generate an operation log
    item_data = deepcopy(item_lib_martigny_data_tmp)
    del item_data['pid']
    item = Item.create(item_data, dbcommit=True, reindex=True)
    flush_index(oplg_index)

    q = f'record.type:item AND record.value:{item.pid}'
    es_url = url_for('invenio_records_rest.oplg_list', q=q, sort='mostrecent')
    login_user_via_session(client, librarian_martigny.user)
    res = client.get(es_url)
    data = get_json(res)
    assert data['hits']['total']['value'] == 1
    metadata = data['hits']['hits'][0]['metadata']
    assert metadata['operation'] == OperationLogOperation.CREATE

    # STEP #2 : Update the item ``price`` attribute.
    #   As any changes on this attribute must be logged, a new operation log
    #   will be generated.
    item['price'] = 10
    item = item.update(item, dbcommit=True, reindex=True)
    flush_index(oplg_index)

    res = client.get(es_url)
    data = get_json(res)
    assert data['hits']['total']['value'] == 2
    metadata = data['hits']['hits'][0]['metadata']
    assert metadata['operation'] == OperationLogOperation.UPDATE

    # STEP #3 : Update the item ``status`` attribute.
    #   This attribute doesn't need to be tracked. So if it's the only change
    #   on this record then no OpLog should be created.
    item['status'] = ItemStatus.EXCLUDED
    item = item.update(item, dbcommit=True, reindex=True)
    flush_index(oplg_index)

    res = client.get(es_url)
    data = get_json(res)
    assert data['hits']['total']['value'] == 2

    # STEP #4 : Update the item ``status`` and ``price`` attributes.
    #   As we update at least one attribute that need to be tracked, this
    #   update will generate a new OpLog (UPDATE)
    item['status'] = ItemStatus.AT_DESK
    item['price'] = 12
    item = item.update(item, dbcommit=True, reindex=True)
    flush_index(oplg_index)

    res = client.get(es_url)
    data = get_json(res)
    assert data['hits']['total']['value'] == 3
    metadata = data['hits']['hits'][0]['metadata']
    assert metadata['operation'] == OperationLogOperation.UPDATE

    # STEP #5 : Delete the item
    #   This will generate the last OpLog about the item.
    item.delete(dbcommit=True, delindex=True)
    flush_index(oplg_index)

    res = client.get(es_url)
    data = get_json(res)
    assert data['hits']['total']['value'] == 4
    metadata = data['hits']['hits'][0]['metadata']
    assert metadata['operation'] == OperationLogOperation.DELETE


def test_operation_log_on_ill_request(client, ill_request_martigny,
                                      librarian_martigny):
    """Test operation log on ILL request."""
    # Using the ``ill_request_martigny`` fixtures, an operation log is created
    # for 'create' operation. Check this operation log to check if special
    # additional informations are included into this OpLog.
    login_user_via_session(client, librarian_martigny.user)

    fake_data = {'date': datetime.now().isoformat()}
    oplg_index = OperationLog.get_index(fake_data)
    flush_index(oplg_index)

    q = f'record.type:illr AND record.value:{ill_request_martigny.pid}'
    es_url = url_for('invenio_records_rest.oplg_list', q=q, sort='mostrecent')
    res = client.get(es_url)
    data = get_json(res)
    assert data['hits']['total']['value'] == 1
    metadata = data['hits']['hits'][0]['metadata']
    assert metadata['operation'] == OperationLogOperation.CREATE
    assert 'ill_request' in metadata
    assert 'status' in metadata['ill_request']
