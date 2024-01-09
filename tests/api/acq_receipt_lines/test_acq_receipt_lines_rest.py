# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
# Copyright (C) 2021 UCLouvain
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

"""Tests REST API acquisition receipt lines."""

import json
from copy import deepcopy

import mock
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import VerifyRecordPermissionPatch, get_json, postdata, \
    to_relative_url

from rero_ils.modules.acquisition.acq_receipt_lines.models import \
    AcqReceiptLineNoteType


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_acq_receipt_lines_get(client, acq_receipt_line_1_fiction_martigny):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.acrl_item', pid_value='acrl1')
    acq_receipt_line = deepcopy(acq_receipt_line_1_fiction_martigny)
    res = client.get(item_url)
    assert res.status_code == 200

    assert res.headers['ETag'] == f'"{acq_receipt_line.revision_id}"'

    data = get_json(res)
    assert acq_receipt_line.dumps() == data['metadata']

    # Check metadata
    for k in ['created', 'updated', 'metadata', 'links']:
        assert k in data

    # Check self links
    res = client.get(to_relative_url(data['links']['self']))
    assert res.status_code == 200
    assert data == get_json(res)
    assert acq_receipt_line.dumps() == data['metadata']

    list_url = url_for('invenio_records_rest.acrl_list', pid='acrl1')
    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)

    metadata = data['hits']['hits'][0]['metadata']

    total_amount = metadata['total_amount']
    assert total_amount == 1000.0

    # remove dynamically added fields
    del metadata['acq_account']
    del metadata['total_amount']
    del metadata['document']
    assert data['hits']['hits'][0]['metadata'] == \
        acq_receipt_line.replace_refs()


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_acq_receipt_lines_post_put_delete(client, org_martigny,
                                           vendor2_martigny,
                                           acq_order_line_fiction_saxon,
                                           acq_receipt_fiction_sion,
                                           acq_receipt_line_fiction_saxon,
                                           json_header):
    """Test record retrieval."""
    # Create record / POST
    item_url = url_for('invenio_records_rest.acrl_item', pid_value='1')
    list_url = url_for('invenio_records_rest.acrl_list', q='pid:1')

    acq_receipt_line_fiction_saxon['pid'] = '1'
    res, data = postdata(
        client,
        'invenio_records_rest.acrl_list',
        acq_receipt_line_fiction_saxon
    )
    assert res.status_code == 201

    # Check that the returned record matches the given data
    assert data['metadata'] == acq_receipt_line_fiction_saxon

    res = client.get(item_url)
    assert res.status_code == 200
    data = get_json(res)
    assert acq_receipt_line_fiction_saxon == data['metadata']

    # Update record/PUT
    data = acq_receipt_line_fiction_saxon
    notes = [{'content': 'test', 'type': AcqReceiptLineNoteType.STAFF}]
    data['notes'] = notes
    res = client.put(
        item_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 200

    # Check that the returned record matches the given data
    data = get_json(res)
    assert data['metadata']['notes'] == notes

    res = client.get(item_url)
    assert res.status_code == 200

    data = get_json(res)
    assert data['metadata']['notes'] == notes

    res = client.get(list_url)
    assert res.status_code == 200

    data = get_json(res)['hits']['hits'][0]
    assert data['metadata']['notes'] == notes

    # Delete record/DELETE
    res = client.delete(item_url)
    assert res.status_code == 204

    res = client.get(item_url)
    assert res.status_code == 410


def test_acq_receipt_lines_can_delete(
        client, document, acq_receipt_line_1_fiction_martigny):
    """Test can delete an acq receipt line."""
    can, reasons = acq_receipt_line_1_fiction_martigny.can_delete
    assert can
    assert 'links' not in reasons


def test_filtered_acq_receipt_lines_get(
        client, librarian_martigny, acq_receipt_line_1_fiction_martigny,
        acq_receipt_line_2_fiction_martigny,
        librarian_sion, acq_receipt_line_fiction_sion):
    """Test acq receipt lines filter by organisation."""
    list_url = url_for('invenio_records_rest.acrl_list')

    res = client.get(list_url)
    assert res.status_code == 401

    # Martigny
    login_user_via_session(client, librarian_martigny.user)
    list_url = url_for('invenio_records_rest.acrl_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total']['value'] == 3

    # Sion
    login_user_via_session(client, librarian_sion.user)
    list_url = url_for('invenio_records_rest.acrl_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total']['value'] == 1
