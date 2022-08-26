# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
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

"""Tests REST API acquisition orders."""

import json

import mock
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import VerifyRecordPermissionPatch, get_json, postdata, \
    to_relative_url

from rero_ils.modules.acquisition.acq_order_lines.models import \
    AcqOrderLineNoteType


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_acq_order_lines_get(client, acq_order_line_fiction_martigny):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.acol_item', pid_value='acol1')
    acol = acq_order_line_fiction_martigny
    res = client.get(item_url)
    data = get_json(res)
    assert res.status_code == 200
    assert res.headers['ETag'] == f'"{acol.revision_id}"'
    assert acol.dumps() == data['metadata']

    # Check metadata
    for k in ['created', 'updated', 'metadata', 'links']:
        assert k in data

    # Check self links
    res = client.get(to_relative_url(data['links']['self']))
    assert res.status_code == 200
    assert data == get_json(res)
    assert acol.dumps() == data['metadata']
    assert data['metadata']['total_amount'] == \
           acol.quantity * acol.get('amount')

    list_url = url_for('invenio_records_rest.acol_list', pid='acol1')
    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)

    metadata = data['hits']['hits'][0]['metadata']
    del metadata['total_unreceived_amount']  # dynamically added key
    del metadata['status']  # dynamically added key
    del metadata['received_quantity']  # dynamically added key
    assert metadata == acol.replace_refs()


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_acq_order_lines_post_put_delete(
        client, org_martigny, vendor2_martigny,
        acq_order_fiction_saxon, acq_order_line_fiction_saxon,
        json_header):
    """Test CRUD on record."""
    # Create record / POST
    item_url = url_for('invenio_records_rest.acol_item', pid_value='1')
    list_url = url_for('invenio_records_rest.acol_list', q='pid:1')

    acq_order_line_fiction_saxon['pid'] = '1'
    res, data = postdata(
        client,
        'invenio_records_rest.acol_list',
        acq_order_line_fiction_saxon
    )
    assert res.status_code == 201

    # Check that the returned record matches the given data
    assert data['metadata'] == acq_order_line_fiction_saxon

    res = client.get(item_url)
    assert res.status_code == 200
    data = get_json(res)
    assert acq_order_line_fiction_saxon == data['metadata']

    # Update record/PUT
    data = acq_order_line_fiction_saxon
    data['notes'] = [{
        'type': AcqOrderLineNoteType.STAFF,
        'content': 'Test update note'
    }]
    res = client.put(
        item_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 200

    # Check that the returned record matches the given data
    data = get_json(res)
    assert data['metadata']['notes'][0]['content'] == 'Test update note'

    res = client.get(item_url)
    assert res.status_code == 200

    data = get_json(res)
    assert data['metadata']['notes'][0]['content'] == 'Test update note'

    res = client.get(list_url)
    assert res.status_code == 200

    data = get_json(res)['hits']['hits'][0]
    assert data['metadata']['notes'][0]['content'] == 'Test update note'

    # Delete record/DELETE
    res = client.delete(item_url)
    assert res.status_code == 204

    res = client.get(item_url)
    assert res.status_code == 410


def test_acq_order_lines_can_delete(client, acq_order_line_fiction_martigny):
    """Test can delete an acq order line."""
    can, reasons = acq_order_line_fiction_martigny.can_delete
    assert can
    assert reasons == {}


def test_acq_order_lines_document_can_delete(
        client, document, acq_order_line_fiction_martigny):
    """Test can delete a document with a linked acquisition order line."""
    can, reasons = document.can_delete
    assert not can
    assert reasons['links']['acq_order_lines']


def test_acq_order_line_secure_api_update(client,
                                          org_sion,
                                          vendor_sion,
                                          acq_order_fiction_sion,
                                          acq_order_line_fiction_sion,
                                          librarian_martigny,
                                          librarian_sion,
                                          json_header):
    """Test acq order line secure api update."""
    # Sion
    login_user_via_session(client, librarian_sion.user)
    record_url = url_for('invenio_records_rest.acol_item',
                         pid_value=acq_order_line_fiction_sion.pid)
    data = acq_order_line_fiction_sion
    data['notes'] = [{
        'type': AcqOrderLineNoteType.STAFF,
        'content': 'Test update note'
    }]
    res = client.put(
        record_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 200
