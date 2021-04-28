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

"""Tests API vendors."""

import json

from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import get_json, postdata


def test_vendors_get(client, librarian_martigny, vendor_martigny):
    """Test vendor record retrieval."""
    # Martigny
    login_user_via_session(client, librarian_martigny.user)
    item_url = url_for(
        'invenio_records_rest.vndr_item',
        pid_value=vendor_martigny.pid)
    list_url = url_for(
        'invenio_records_rest.vndr_list',
        q='pid:{pid}'.format(pid=vendor_martigny.pid))

    res = client.get(item_url)
    assert res.status_code == 200

    assert res.headers['ETag'] == '"{}"'.format(vendor_martigny.revision_id)

    data = get_json(res)
    assert vendor_martigny.dumps() == data['metadata']

    # Check metadata
    for k in ['created', 'updated', 'metadata', 'links']:
        assert k in data


def test_filtered_vendors_get(client, librarian_martigny,
                              librarian_sion, vendor_martigny,
                              vendor2_martigny, vendor_sion, vendor2_sion):
    """Test vendors filter by organisation."""
    # Martigny
    login_user_via_session(client, librarian_martigny.user)
    list_url = url_for('invenio_records_rest.vndr_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total']['value'] == 2

    # Sion
    login_user_via_session(client, librarian_sion.user)
    list_url = url_for('invenio_records_rest.vndr_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total']['value'] == 2


def test_vendors_can_delete(
        client, vendor_martigny, acq_order_fiction_martigny,
        acq_invoice_fiction_martigny, holding_lib_martigny_w_patterns):
    """Test can delete a vendor with a linked acquisition order."""
    assert not vendor_martigny.can_delete

    reasons = vendor_martigny.reasons_not_to_delete()
    assert reasons['links']['acq_orders']
    assert reasons['links']['acq_invoices']
    assert reasons['links']['holdings']


def test_vendor_post_update_delete(client, librarian_martigny,
                                   vendor3_martigny_data, json_header):
    """Test CRUD on vendor."""
    login_user_via_session(client, librarian_martigny.user)
    item_url = url_for('invenio_records_rest.vndr_item', pid_value='vndr3')

    # create
    vendor3_martigny_data['pid'] = 'vndr3'
    res, data = postdata(
        client,
        'invenio_records_rest.vndr_list',
        vendor3_martigny_data
    )
    assert res.status_code == 201

    # read
    res = client.get(item_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['metadata'] == vendor3_martigny_data

    # update
    data = vendor3_martigny_data
    data['name'] = 'Test update Name'
    res = client.put(
        item_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 200

    # Check that the returned record matches the given data
    data = get_json(res)
    assert data['metadata']['name'] == 'Test update Name'

    # delete
    res = client.delete(item_url)
    assert res.status_code == 204

    res = client.get(item_url)
    assert res.status_code == 410
