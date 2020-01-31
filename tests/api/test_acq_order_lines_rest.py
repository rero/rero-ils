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


def test_acq_orders_lines_permissions(
        client, document, acq_order_line_fiction_martigny, json_header):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.acol_item', pid_value='acol1')

    res = client.get(item_url)
    assert res.status_code == 401

    res, _ = postdata(
        client,
        'invenio_records_rest.acol_list',
        {}
    )
    assert res.status_code == 401

    res = client.put(
        url_for('invenio_records_rest.acol_item', pid_value='acol1'),
        data={},
        headers=json_header
    )

    res = client.delete(item_url)
    assert res.status_code == 401


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_acq_order_lines_get(client, acq_order_line_fiction_martigny):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.acol_item', pid_value='acol1')
    acq_order_line = acq_order_line_fiction_martigny
    res = client.get(item_url)
    assert res.status_code == 200

    assert res.headers['ETag'] == '"{}"'.format(acq_order_line.revision_id)

    data = get_json(res)
    assert acq_order_line.dumps() == data['metadata']

    # Check metadata
    for k in ['created', 'updated', 'metadata', 'links']:
        assert k in data

    # Check self links
    res = client.get(to_relative_url(data['links']['self']))
    assert res.status_code == 200
    assert data == get_json(res)
    assert acq_order_line.dumps() == data['metadata']

    assert data['metadata']['total_amount'] == 1000

    list_url = url_for('invenio_records_rest.acol_list', pid='acol1')
    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)

    assert data['hits']['hits'][0]['metadata'] == acq_order_line.replace_refs()


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
    data['note'] = 'Test update note'
    res = client.put(
        item_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 200

    # Check that the returned record matches the given data
    data = get_json(res)
    assert data['metadata']['note'] == 'Test update note'

    res = client.get(item_url)
    assert res.status_code == 200

    data = get_json(res)
    assert data['metadata']['note'] == 'Test update note'

    res = client.get(list_url)
    assert res.status_code == 200

    data = get_json(res)['hits']['hits'][0]
    assert data['metadata']['note'] == 'Test update note'

    # Delete record/DELETE
    res = client.delete(item_url)
    assert res.status_code == 204

    res = client.get(item_url)
    assert res.status_code == 410


def test_acq_order_lines_can_delete(client, acq_order_line_fiction_martigny):
    """Test can delete an acq order line."""
    links = acq_order_line_fiction_martigny.get_links_to_me()
    assert not links

    assert acq_order_line_fiction_martigny.can_delete

    reasons = acq_order_line_fiction_martigny.reasons_not_to_delete()
    assert not reasons


def test_acq_order_lines_document_can_delete(
        client, document, acq_order_line_fiction_martigny):
    """Test can delete a document with a linked acquisition order line."""
    assert not document.can_delete

    reasons = document.reasons_not_to_delete()
    assert reasons['links']['acq_order_lines']


def test_acq_order_line_secure_api(client, json_header,
                                   acq_order_line_fiction_martigny,
                                   librarian_martigny_no_email,
                                   librarian_sion_no_email):
    """Test acq order line secure api access."""
    # Martigny
    login_user_via_session(client, librarian_martigny_no_email.user)
    record_url = url_for('invenio_records_rest.acol_item',
                         pid_value=acq_order_line_fiction_martigny.pid)

    res = client.get(record_url)
    assert res.status_code == 200

    # Sion
    login_user_via_session(client, librarian_sion_no_email.user)
    record_url = url_for('invenio_records_rest.acol_item',
                         pid_value=acq_order_line_fiction_martigny.pid)

    res = client.get(record_url)
    assert res.status_code == 403


def test_acq_order_secure_api_create(client, json_header,
                                     org_martigny,
                                     vendor_martigny, vendor2_martigny,
                                     acq_order_line_fiction_martigny,
                                     librarian_martigny_no_email,
                                     librarian_sion_no_email,
                                     acq_order_line_fiction_saxon,
                                     system_librarian_martigny_no_email):
    """Test acq order line secure api create."""
    # Martigny
    login_user_via_session(client, librarian_martigny_no_email.user)
    post_entrypoint = 'invenio_records_rest.acol_list'

    data = acq_order_line_fiction_saxon
    del data['pid']
    res, _ = postdata(
        client,
        post_entrypoint,
        data
    )
    assert res.status_code == 403

    data = acq_order_line_fiction_martigny
    del data['pid']
    res, _ = postdata(
        client,
        post_entrypoint,
        data
    )
    assert res.status_code == 201

    login_user_via_session(client, system_librarian_martigny_no_email.user)
    res, _ = postdata(
        client,
        post_entrypoint,
        data
    )
    assert res.status_code == 201

    # Sion
    login_user_via_session(client, librarian_sion_no_email.user)

    data = acq_order_line_fiction_saxon
    res, _ = postdata(
        client,
        post_entrypoint,
        data
    )
    assert res.status_code == 403


def test_acq_order_line_secure_api_update(client,
                                          org_sion,
                                          vendor_sion,
                                          acq_order_fiction_sion,
                                          acq_order_line_fiction_sion,
                                          librarian_martigny_no_email,
                                          librarian_sion_no_email,
                                          json_header):
    """Test acq order line secure api update."""
    # Sion
    login_user_via_session(client, librarian_sion_no_email.user)
    record_url = url_for('invenio_records_rest.acol_item',
                         pid_value=acq_order_line_fiction_sion.pid)
    data = acq_order_line_fiction_sion
    data['note'] = 'Test update note'
    res = client.put(
        record_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 200

    # Martigny
    login_user_via_session(client, librarian_martigny_no_email.user)

    res = client.put(
        record_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 403
