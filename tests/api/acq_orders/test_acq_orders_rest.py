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
from copy import deepcopy

import mock
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import VerifyRecordPermissionPatch, get_json, postdata, \
    to_relative_url

from rero_ils.modules.acq_orders.models import AcqOrderStatus


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_acq_orders_library_facets(
    client, org_martigny, acq_order_fiction_martigny, rero_json_header
):
    """Test record retrieval."""
    url = url_for('invenio_records_rest.acor_list', view='org1')
    res = client.get(url, headers=rero_json_header)
    data = get_json(res)
    facets = ['library', 'vendor', 'type', 'status', 'account', 'order_date']
    assert all(facet_name in data['aggregations'] for facet_name in facets)


def test_acq_orders_permissions(client, acq_order_fiction_martigny,
                                json_header):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.acor_item', pid_value='acor1')

    res = client.get(item_url)
    assert res.status_code == 401

    res, _ = postdata(
        client,
        'invenio_records_rest.acor_list',
        {}
    )
    assert res.status_code == 401

    res = client.put(
        url_for('invenio_records_rest.acor_item', pid_value='acor1'),
        data={},
        headers=json_header
    )

    res = client.delete(item_url)
    assert res.status_code == 401


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_acq_order_get(client, acq_order_fiction_martigny):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.acor_item', pid_value='acor1')
    acq_order = deepcopy(acq_order_fiction_martigny)
    res = client.get(item_url)
    assert res.status_code == 200

    assert res.headers['ETag'] == '"{}"'.format(acq_order.revision_id)

    data = get_json(res)
    assert acq_order.dumps() == data['metadata']

    # Check metadata
    for k in ['created', 'updated', 'metadata', 'links']:
        assert k in data

    # Check self links
    res = client.get(to_relative_url(data['links']['self']))
    assert res.status_code == 200
    assert data == get_json(res)
    assert acq_order.dumps() == data['metadata']

    assert acq_order.get_account_statement() == \
           data['metadata']['account_statement']

    list_url = url_for('invenio_records_rest.acor_list', pid='acor1')
    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)

    metadata = data['hits']['hits'][0]['metadata']
    # remove dynamically added fields
    del metadata['organisation']
    del metadata['order_lines']
    del metadata['receipts']
    assert data['hits']['hits'][0]['metadata'] == acq_order.replace_refs()


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_acq_orders_post_put_delete(client, org_martigny, vendor2_martigny,
                                    acq_order_fiction_saxon,
                                    json_header):
    """Test record retrieval."""
    # Create record / POST
    item_url = url_for('invenio_records_rest.acor_item', pid_value='1')
    list_url = url_for('invenio_records_rest.acor_list', q='pid:1')

    acq_order_fiction_saxon['pid'] = '1'
    res, data = postdata(
        client,
        'invenio_records_rest.acor_list',
        acq_order_fiction_saxon
    )
    assert res.status_code == 201

    # Check that the returned record matches the given data
    assert data['metadata'].pop('account_statement') == {
        'provisional': {
            'total_amount': 0,
            'quantity': 0
        },
        'expenditure': {
            'total_amount': 0,
            'quantity': 0
        }
    }
    assert data['metadata'].pop('status') == AcqOrderStatus.PENDING
    assert not data['metadata'].pop('order_date', None)
    assert data['metadata'] == acq_order_fiction_saxon

    res = client.get(item_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['metadata'].pop('account_statement') == {
        'provisional': {
            'total_amount': 0,
            'quantity': 0
        },
        'expenditure': {
            'total_amount': 0,
            'quantity': 0
        }
    }
    assert data['metadata'].pop('status') == AcqOrderStatus.PENDING
    assert not data['metadata'].pop('order_date', None)
    assert acq_order_fiction_saxon == data['metadata']

    # Update record/PUT
    data = acq_order_fiction_saxon
    data['reference'] = 'Test reference'
    res = client.put(
        item_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 200

    # Check that the returned record matches the given data
    data = get_json(res)
    assert data['metadata']['reference'] == 'Test reference'

    res = client.get(item_url)
    assert res.status_code == 200

    data = get_json(res)
    assert data['metadata']['reference'] == 'Test reference'

    res = client.get(list_url)
    assert res.status_code == 200

    data = get_json(res)['hits']['hits'][0]
    assert data['metadata']['reference'] == 'Test reference'

    # Delete record/DELETE
    res = client.delete(item_url)
    assert res.status_code == 204

    res = client.get(item_url)
    assert res.status_code == 410


def test_acq_orders_can_delete(
        client, document, acq_order_fiction_martigny,
        acq_order_line_fiction_martigny, acq_receipt_fiction_martigny):
    """Test can delete an acq order."""
    can, reasons = acq_order_fiction_martigny.can_delete
    assert not can
    assert reasons['links']['receipts']


def test_filtered_acq_orders_get(
        client, librarian_martigny, acq_order_fiction_martigny,
        librarian_sion, acq_order_fiction_sion):
    """Test acq accounts filter by organisation."""
    list_url = url_for('invenio_records_rest.acor_list')

    res = client.get(list_url)
    assert res.status_code == 401

    # Martigny
    login_user_via_session(client, librarian_martigny.user)
    list_url = url_for('invenio_records_rest.acor_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total']['value'] == 2

    # Sion
    login_user_via_session(client, librarian_sion.user)
    list_url = url_for('invenio_records_rest.acor_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total']['value'] == 1


def test_acq_order_secure_api(client, json_header,
                              acq_order_fiction_martigny,
                              librarian_martigny,
                              librarian_sion):
    """Test acq order secure api access."""
    # Martigny
    login_user_via_session(client, librarian_martigny.user)
    record_url = url_for('invenio_records_rest.acor_item',
                         pid_value=acq_order_fiction_martigny.pid)

    res = client.get(record_url)
    assert res.status_code == 200

    # Sion
    login_user_via_session(client, librarian_sion.user)
    record_url = url_for('invenio_records_rest.acor_item',
                         pid_value=acq_order_fiction_martigny.pid)

    res = client.get(record_url)
    assert res.status_code == 403


def test_acq_order_secure_api_create(client, json_header,
                                     org_martigny,
                                     vendor_martigny, vendor2_martigny,
                                     acq_order_fiction_martigny,
                                     librarian_martigny,
                                     librarian_sion,
                                     acq_order_fiction_saxon,
                                     system_librarian_martigny):
    """Test acq order secure api create."""
    # Martigny
    login_user_via_session(client, librarian_martigny.user)
    post_entrypoint = 'invenio_records_rest.acor_list'

    data = acq_order_fiction_saxon
    del acq_order_fiction_saxon['pid']
    res, _ = postdata(
        client,
        post_entrypoint,
        data
    )
    assert res.status_code == 403

    data = deepcopy(acq_order_fiction_martigny)
    del data['pid']
    res, _ = postdata(
        client,
        post_entrypoint,
        data
    )
    assert res.status_code == 201

    login_user_via_session(client, system_librarian_martigny.user)
    res, _ = postdata(
        client,
        post_entrypoint,
        data
    )
    assert res.status_code == 201

    # Sion
    login_user_via_session(client, librarian_sion.user)

    res, _ = postdata(
        client,
        post_entrypoint,
        acq_order_fiction_saxon
    )
    assert res.status_code == 403


def test_acq_order_secure_api_update(client,
                                     org_sion,
                                     vendor_sion,
                                     acq_order_fiction_sion,
                                     librarian_martigny,
                                     librarian_sion,
                                     json_header):
    """Test acq order secure api update."""
    # Sion
    login_user_via_session(client, librarian_sion.user)
    record_url = url_for('invenio_records_rest.acor_item',
                         pid_value=acq_order_fiction_sion.pid)
    data = acq_order_fiction_sion
    data['reference'] = 'Test update reference'
    res = client.put(
        record_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 200

    # Martigny
    login_user_via_session(client, librarian_martigny.user)

    res = client.put(
        record_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 403
