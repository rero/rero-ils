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

import pytest
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from invenio_records.api import Record
from jsonref import JsonRefError
from utils import get_json, postdata


def test_vendors_get(client, librarian_martigny_no_email, vendor_martigny):
    """Test vendor record retrieval."""
    # Martigny
    login_user_via_session(client, librarian_martigny_no_email.user)
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


def test_filtered_vendors_get(client, librarian_martigny_no_email,
                              librarian_sion_no_email, vendor_martigny,
                              vendor2_martigny, vendor_sion, vendor2_sion):
    """Test vendors filter by organisation."""
    # Martigny
    login_user_via_session(client, librarian_martigny_no_email.user)
    list_url = url_for('invenio_records_rest.vndr_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total'] == 2

    # Sion
    login_user_via_session(client, librarian_sion_no_email.user)
    list_url = url_for('invenio_records_rest.vndr_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total'] == 2


def test_vendor_post_update_delete(client, librarian_martigny_no_email,
                                   vendor_martigny_data, json_header):
    """Test CRUD on vendor."""
    login_user_via_session(client, librarian_martigny_no_email.user)
    item_url = url_for('invenio_records_rest.vndr_item', pid_value='vndr1')

    # create
    res, data = postdata(
        client,
        'invenio_records_rest.vndr_list',
        vendor_martigny_data
    )
    assert res.status_code == 201

    # read
    res = client.get(item_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['metadata'] == vendor_martigny_data

    # update
    data = vendor_martigny_data
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


def test_vendors_jsonresolver(app, vendor_martigny_tmp):
    """Test vendor resolver."""
    rec = Record.create({
        'vendor': {'$ref': 'https://ils.rero.ch/api/vendors/1'}
    })
    assert rec.replace_refs().get('vendor') == {'pid': '1'}

    # deleted record
    vendor_martigny_tmp.delete()
    with pytest.raises(Exception):
        rec.replace_refs().dumps()

    # non existing record
    rec = Record.create({
        'vendor': {'$ref': 'https://ils.rero.ch/api/vendors/n_e'}
    })

    with pytest.raises(JsonRefError) as error:
        rec.replace_refs().dumps()
    assert 'PIDDoesNotExistError' in str(error)
