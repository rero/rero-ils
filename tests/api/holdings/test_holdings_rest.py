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

"""Tests REST API holdings."""


import json

import mock
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import VerifyRecordPermissionPatch, get_json, postdata, \
    to_relative_url

from rero_ils.modules.holdings.api import Holding


def test_holding_can_delete_and_utils(client, holding_lib_martigny, document,
                                      item_type_standard_martigny):
    """Test can delete a holding."""
    can, reasons = holding_lib_martigny.can_delete
    assert can
    assert reasons == {}

    assert holding_lib_martigny.document_pid == document.pid
    assert holding_lib_martigny.circulation_category_pid == \
        item_type_standard_martigny.pid
    assert Holding.get_document_pid_by_holding_pid(
        holding_lib_martigny.pid) == document.pid
    assert list(Holding.get_holdings_pid_by_document_pid(document.pid))[0] == \
        holding_lib_martigny.pid


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_holdings_get(
    client, item_lib_martigny, item_lib_martigny_masked, rero_json_header
):
    """Test record retrieval."""
    holding = Holding.get_record_by_pid(item_lib_martigny.holding_pid)
    url = url_for('invenio_records_rest.hold_item', pid_value=holding.pid)

    # Check REST API for a single holdings
    res = client.get(url)
    assert res.status_code == 200
    assert res.headers['ETag'] == f'"{holding.revision_id}"'
    data = get_json(res)
    assert all(k in data for k in ['created', 'updated', 'metadata', 'links'])
    assert holding.dumps() == data['metadata']

    # Check self links
    res = client.get(to_relative_url(data['links']['self']))
    assert res.status_code == 200
    assert data == get_json(res)
    assert holding.dumps() == data['metadata']

    # Check REST API for a single holdings with reference resolver
    url = url_for('invenio_records_rest.hold_item', pid_value=holding.pid,
                  resolve=1, sources=1)
    res = client.get(url)
    assert res.status_code == 200
    data = get_json(res)
    assert holding.replace_refs().dumps() == data['metadata']

    # Check REST API for holdings query
    url = url_for('invenio_records_rest.hold_list', q=f'pid:{holding.pid}')
    res = client.get(url)
    assert res.status_code == 200
    data = get_json(res)
    hit = data['hits']['hits'][0]['metadata']
    assert hit.pop('public_items_count') == 1
    assert hit.pop('items_count') == 2
    assert hit == holding.replace_refs()

    # Check REST API for holdings query for `rero+json` header
    res = client.get(url, headers=rero_json_header)
    assert res.status_code == 200
    data = get_json(res)
    hit = data['hits']['hits'][0]['metadata']


def test_filtered_holdings_get(
        client, librarian_martigny, holding_lib_martigny,
        holding_lib_fully, holding_lib_saxon, holding_lib_sion,
        patron_sion):
    """Test holding filter by organisation."""
    # Librarian Martigny
    login_user_via_session(client, librarian_martigny.user)
    list_url = url_for('invenio_records_rest.hold_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total']['value'] == 4

    # Patron Martigny
    login_user_via_session(client, patron_sion.user)
    list_url = url_for('invenio_records_rest.hold_list', view='org2')
    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total']['value'] == 1


def test_holdings_items_filter(client, holding_lib_martigny, holding_lib_sion,
                               item_lib_martigny):
    """Test filter for holdings items."""
    assert len(
        holding_lib_martigny.get_items_filter_by_viewcode('global')) == 1

    assert len(
        holding_lib_martigny.get_items_filter_by_viewcode('org2')) == 0


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_holdings_post_put_delete(client, holding_lib_martigny_data_tmp,
                                  json_header, holding_lib_martigny,
                                  loc_public_martigny):
    """Test record create and delete."""
    item_url = url_for('invenio_records_rest.hold_item', pid_value='2')
    list_url = url_for('invenio_records_rest.hold_list', q='pid:2')
    holding_data = holding_lib_martigny_data_tmp
    # Create record / POST
    # We can not use pid=1 here. It is already used!
    holding_data['pid'] = '2'
    res, data = postdata(
        client,
        'invenio_records_rest.hold_list',
        holding_data
    )
    assert res.status_code == 201

    # Check that the returned record matches the given data
    assert data['metadata'] == holding_data

    res = client.get(item_url)
    assert res.status_code == 200
    data = get_json(res)
    assert holding_data == data['metadata']

    # Update record/PUT
    data = holding_data
    data['call_number'] = 'call number'
    res = client.put(
        item_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 200

    # Check that the returned record matches the given data
    data = get_json(res)
    assert data['metadata']['call_number'] == 'call number'

    res = client.get(item_url)
    assert res.status_code == 200

    data = get_json(res)
    assert data['metadata']['call_number'] == 'call number'

    res = client.get(list_url)
    assert res.status_code == 200

    data = get_json(res)['hits']['hits'][0]
    assert data['metadata']['call_number'] == 'call number'

    # Delete record/DELETE
    res = client.delete(item_url)
    assert res.status_code == 204

    res = client.get(item_url)
    assert res.status_code == 410


def test_holding_request(client, librarian_martigny, patron_martigny,
                         holding_lib_martigny, holding_lib_martigny_w_patterns,
                         lib_martigny, circ_policy_short_martigny):
    """Test holding can be requested"""
    # test patron can request holding
    login_user_via_session(client, patron_martigny.user)
    patron = patron_martigny

    res = client.get(
        url_for(
            'api_holding.can_request',
            holding_pid=holding_lib_martigny_w_patterns.pid,
            library_pid=lib_martigny.pid,
            patron_barcode=patron.patron.get('barcode')
        )
    )
    response = json.loads(res.data)
    assert response['can']

    # test librarian can request holding
    login_user_via_session(client, librarian_martigny.user)
    patron = librarian_martigny

    res = client.get(
        url_for(
            'api_holding.can_request',
            holding_pid=holding_lib_martigny_w_patterns.pid,
            library_pid=lib_martigny.pid,
            patron_barcode=patron.patron.get('barcode')
        )
    )
    response = json.loads(res.data)
    assert response['can']

    # test patron cannot request holding
    login_user_via_session(client, patron_martigny.user)
    patron = patron_martigny

    res = client.get(
        url_for(
            'api_holding.can_request',
            holding_pid=holding_lib_martigny.pid,
            library_pid=lib_martigny.pid,
            patron_barcode=patron.patron.get('barcode')
        )
    )
    response = json.loads(res.data)
    assert not response['can']

    # test librarian cannot request holding
    login_user_via_session(client, librarian_martigny.user)
    patron = librarian_martigny

    res = client.get(
        url_for(
            'api_holding.can_request',
            holding_pid=holding_lib_martigny.pid,
            library_pid=lib_martigny.pid,
            patron_barcode=patron.patron.get('barcode')
        )
    )
    response = json.loads(res.data)
    assert not response['can']
