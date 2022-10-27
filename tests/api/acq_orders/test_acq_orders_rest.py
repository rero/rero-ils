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
from api.acquisition.acq_utils import _del_resource, _make_resource
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import VerifyRecordPermissionPatch, get_json, postdata, \
    to_relative_url

from rero_ils.modules.acquisition.acq_orders.models import AcqOrderStatus
from rero_ils.modules.utils import get_ref_for_pid


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


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_acq_order_get(client, acq_order_fiction_martigny):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.acor_item', pid_value='acor1')
    acq_order = deepcopy(acq_order_fiction_martigny)
    res = client.get(item_url)
    assert res.status_code == 200

    assert res.headers['ETag'] == f'"{acq_order.revision_id}"'

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
    metadata.pop('budget', None)
    assert data['hits']['hits'][0]['metadata'] == acq_order.replace_refs()


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_acq_orders_post_put_delete(
    client, org_martigny, vendor2_martigny, acq_order_fiction_saxon,
    acq_order_fiction_saxon_data, json_header
):
    """Test record retrieval."""
    # Create record / POST
    acq_order_fiction_saxon_data.pop('pid', None)
    res, data = postdata(
        client,
        'invenio_records_rest.acor_list',
        acq_order_fiction_saxon_data
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
    acq_order_fiction_saxon_data['pid'] = data['metadata']['pid']
    assert data['metadata'] == acq_order_fiction_saxon_data

    pid = data['metadata']['pid']
    item_url = url_for('invenio_records_rest.acor_item', pid_value=pid)
    list_url = url_for('invenio_records_rest.acor_list', q=f'pid:{pid}')

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
    assert acq_order_fiction_saxon_data == data['metadata']

    # Update record/PUT
    api_data = acq_order_fiction_saxon_data
    api_data['reference'] = 'Test reference'
    res = client.put(
        item_url,
        data=json.dumps(api_data),
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


def test_acq_order_history_api(
  client, vendor_martigny, lib_martigny, rero_json_header, librarian_martigny,
  acq_account_fiction_martigny, document, budget_2020_martigny
):
    """Test acquisition order history API."""
    login_user_via_session(client, librarian_martigny.user)
    # STEP#0 :: create order related to each other.
    data = {
        'vendor': {'$ref': get_ref_for_pid('vndr', vendor_martigny.pid)},
        'library': {'$ref': get_ref_for_pid('lib', lib_martigny.pid)},
        'type': 'monograph',
    }
    acor1 = _make_resource(client, 'acor', data)
    data['previousVersion'] = {'$ref': get_ref_for_pid('acor', acor1.pid)}
    acor2 = _make_resource(client, 'acor', data)
    data['previousVersion'] = {'$ref': get_ref_for_pid('acor', acor2.pid)}
    acor3 = _make_resource(client, 'acor', data)

    # add an order line to any order. This will change the order history item
    # label ; the label should be set to order line related budget name
    acac = acq_account_fiction_martigny
    data = {
        'acq_account': {'$ref': get_ref_for_pid('acac', acac.pid)},
        'acq_order': {'$ref': get_ref_for_pid('acor', acor2.pid)},
        'document': {'$ref': get_ref_for_pid('doc', document.pid)},
        'quantity': 2,
        'amount': 50
    }
    acol1 = _make_resource(client, 'acol', data)

    # STEP#1 :: Call API and analyze response
    #  * with unknown acquisition order --> 404
    #  * with valid acquisition order --> valid response
    url = url_for('api_order.order_history', order_pid='dummy')
    res = client.get(url, headers=rero_json_header)
    assert res.status_code == 404

    url = url_for('api_order.order_history', order_pid=acor2.pid)
    res = client.get(url, headers=rero_json_header)
    data = get_json(res)

    assert len(data) == 3
    assert data[0]['$ref'] == get_ref_for_pid('acor', acor1.pid)
    assert data[1]['$ref'] == get_ref_for_pid('acor', acor2.pid)
    assert data[1]['label'] == budget_2020_martigny.name
    assert data[2]['$ref'] == get_ref_for_pid('acor', acor3.pid)

    # STEP#2 :: Ensure a linked order cannot be deleted
    reasons = acor2.reasons_not_to_delete()
    assert reasons['links']['orders'] == 1

    # STEP#X :: delete created resources
    _del_resource(client, 'acol', acol1.pid)
    _del_resource(client, 'acor', acor3.pid)
    _del_resource(client, 'acor', acor2.pid)
    _del_resource(client, 'acor', acor1.pid)
