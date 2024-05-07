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
from flask import current_app, url_for
from invenio_access.permissions import system_identity
from invenio_accounts.testutils import login_user_via_session
from utils import VerifyRecordPermissionPatch, flush_index, get_json, postdata

from rero_ils.modules.documents.api import DocumentsSearch
from rero_ils.modules.files.cli import create_pdf_record_files
from rero_ils.modules.items.api import Item
from rero_ils.modules.items.models import ItemStatus
from rero_ils.modules.operation_logs.api import OperationLog
from rero_ils.modules.operation_logs.models import OperationLogOperation
from rero_ils.modules.utils import get_ref_for_pid


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


def test_operation_log_on_file(
    client, librarian_martigny, document, lib_martigny, file_location
):
    """Test files operation log."""

    # get the op index
    fake_data = {'date': datetime.now().isoformat()}
    oplg_index = OperationLog.get_index(fake_data)

    # create a pdf file
    metadata = dict(
        library={'$ref': get_ref_for_pid('lib', lib_martigny.pid)},
        collections=['col1', 'col2']
    )
    record = create_pdf_record_files(document, metadata, flush=True)
    recid = record["id"]

    # get services
    ext = current_app.extensions["rero-invenio-files"]
    file_service = ext.records_files_service
    record_service = ext.records_service

    # flush indices
    flush_index(DocumentsSearch.Meta.index)
    flush_index(oplg_index)

    # REST API are restricted, thus it needs a login
    login_user_via_session(client, librarian_martigny.user)

    # record file creation is in the op
    es_url = url_for(
        'invenio_records_rest.oplg_list',
        q=f'record.type:recid AND operation:create')
    res = client.get(es_url)
    data = get_json(res)
    assert data['hits']['total']['value'] == 1
    metadata = data['hits']['hits'][0]['metadata']
    assert set(metadata['record'].keys()) == \
        set(['library_pid', 'organisation_pid', 'type', 'value'])
    assert set(metadata['file']['document']) == {'pid', 'type', 'title'}

    # record file update is in the op
    record_service.update(
        system_identity, recid, dict(metadata=record['metadata']))
    flush_index(oplg_index)
    es_url = url_for(
        'invenio_records_rest.oplg_list',
        q=f'record.type:recid AND operation:update')
    res = client.get(es_url)
    data = get_json(res)
    assert data['hits']['total']['value'] == 1

    # file creation is in the op
    pdf_file_name = 'doc_doc1_1.pdf'
    es_url = url_for(
        'invenio_records_rest.oplg_list',
        q='record.type:file AND operation:create '
          f'AND record.value:{pdf_file_name}')
    res = client.get(es_url)
    data = get_json(res)
    metadata = data['hits']['hits'][0]['metadata']
    assert data['hits']['total']['value'] == 1
    assert set(data['hits']['hits'][0]['metadata']['record'].keys()) == \
        set(['library_pid', 'organisation_pid', 'type', 'value'])
    assert set(metadata['file']['document']) == {'pid', 'type', 'title'}
    assert metadata['file']['recid'] == recid

    # file deletion is in the op
    file_service.delete_file(
        identity=system_identity, id_=recid, file_key=pdf_file_name)
    flush_index(oplg_index)

    es_url = url_for(
        'invenio_records_rest.oplg_list',
        q='record.type:file AND operation:delete '
          f'AND record.value:{pdf_file_name}')
    res = client.get(es_url)
    data = get_json(res)
    assert data['hits']['total']['value'] == 1

    # record file deletion is in the op
    record_service.delete(identity=system_identity, id_=recid)
    flush_index(oplg_index)
    es_url = url_for(
        'invenio_records_rest.oplg_list',
        q=f'record.type:recid AND operation:delete')
    res = client.get(es_url)
    data = get_json(res)
    assert data['hits']['total']['value'] == 1
