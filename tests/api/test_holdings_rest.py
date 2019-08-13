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
from copy import deepcopy

import mock
import pytest
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import VerifyRecordPermissionPatch, flush_index, get_json, \
    to_relative_url

from rero_ils.modules.api import IlsRecordError
from rero_ils.modules.holdings.api import Holding, HoldingsSearch


def test_holdings_permissions(client, holding_lib_martigny, json_header):
    """Test record permissions."""
    item_url = url_for('invenio_records_rest.hold_item', pid_value='holding1')
    post_url = url_for('invenio_records_rest.hold_list')

    res = client.get(item_url)
    assert res.status_code == 401

    res = client.post(
        post_url,
        data={},
        headers=json_header
    )
    assert res.status_code == 401

    res = client.put(
        item_url,
        data={},
        headers=json_header
    )

    res = client.delete(item_url)
    assert res.status_code == 401


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_holdings_get(client, holding_lib_martigny):
    """Test record retrieval."""
    holding = holding_lib_martigny
    item_url = url_for('invenio_records_rest.hold_item', pid_value=holding.pid)
    list_url = url_for(
        'invenio_records_rest.hold_list', q='pid:' + holding.pid)
    item_url_with_resolve = url_for(
        'invenio_records_rest.hold_item',
        pid_value=holding.pid,
        resolve=1,
        sources=1
    )

    res = client.get(item_url)
    assert res.status_code == 200

    assert res.headers['ETag'] == '"{}"'.format(holding.revision_id)

    data = get_json(res)
    assert holding.dumps() == data['metadata']

    # Check metadata
    for k in ['created', 'updated', 'metadata', 'links']:
        assert k in data

    # Check self links
    res = client.get(to_relative_url(data['links']['self']))
    assert res.status_code == 200
    assert data == get_json(res)
    assert holding.dumps() == data['metadata']

    # check resolve
    res = client.get(item_url_with_resolve)
    assert res.status_code == 200
    data = get_json(res)
    assert holding.replace_refs().dumps() == data['metadata']

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    result = data['hits']['hits'][0]['metadata']
    # organisation has been added during the indexing
    del result['organisation']
    assert result == holding.replace_refs()


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_holdings_post_put_delete(client, holding_lib_martigny_data_tmp,
                                  json_header, holding_lib_martigny,
                                  loc_public_martigny):
    """Test record create and delete."""
    item_url = url_for('invenio_records_rest.hold_item', pid_value='1')
    post_url = url_for('invenio_records_rest.hold_list')
    list_url = url_for('invenio_records_rest.hold_list', q='pid:1')
    holding_data = holding_lib_martigny_data_tmp
    # Create record / POST
    holding_data['pid'] = '1'
    res = client.post(
        post_url,
        data=json.dumps(holding_data),
        headers=json_header
    )
    assert res.status_code == 201

    flush_index(HoldingsSearch.Meta.index)

    # Check that the returned record matches the given data
    data = get_json(res)
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


def test_holding_can_delete_and_utils(client, holding_lib_martigny, document,
                                      item_type_standard_martigny):
    """Test can delete a holding."""
    links = holding_lib_martigny.get_links_to_me()
    assert 'items' not in links

    assert holding_lib_martigny.can_delete

    reasons = holding_lib_martigny.reasons_not_to_delete()
    assert 'links' not in reasons

    assert holding_lib_martigny.document_pid == document.pid
    assert holding_lib_martigny.circulation_category_pid == \
        item_type_standard_martigny.pid
    assert Holding.get_document_pid_by_holding_pid(
        holding_lib_martigny.pid) == document.pid
    assert list(Holding.get_holdings_pid_by_document_pid(document.pid))[0] == \
        holding_lib_martigny.pid


def test_filtered_holdings_get(
        client, librarian_martigny_no_email, holding_lib_martigny,
        holding_lib_fully, holding_lib_saxon, holding_lib_sion,
        librarian_sion_no_email):
    """Test holding filter by organisation."""
    # Martigny
    login_user_via_session(client, librarian_martigny_no_email.user)
    list_url = url_for('invenio_records_rest.hold_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total'] == 3

    # Sion
    login_user_via_session(client, librarian_sion_no_email.user)
    list_url = url_for('invenio_records_rest.hold_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total'] == 1


def test_holding_secure_api(client, json_header, holding_lib_martigny,
                            librarian_martigny_no_email,
                            librarian_sion_no_email):
    """Test holding secure api access."""
    # Martigny
    login_user_via_session(client, librarian_martigny_no_email.user)
    record_url = url_for('invenio_records_rest.hold_item',
                         pid_value=holding_lib_martigny.pid)

    res = client.get(record_url)
    assert res.status_code == 200

    # Sion
    login_user_via_session(client, librarian_sion_no_email.user)
    record_url = url_for('invenio_records_rest.hold_item',
                         pid_value=holding_lib_martigny.pid)

    res = client.get(record_url)
    assert res.status_code == 403


def test_holding_secure_api_create(client, json_header, holding_lib_martigny,
                                   librarian_martigny_no_email,
                                   librarian_sion_no_email,
                                   holding_lib_martigny_data):
    """Test holding secure api create."""
    # Martigny
    login_user_via_session(client, librarian_martigny_no_email.user)
    post_url = url_for('invenio_records_rest.hold_list')

    del holding_lib_martigny_data['pid']
    res = client.post(
        post_url,
        data=json.dumps(holding_lib_martigny_data),
        headers=json_header
    )
    assert res.status_code == 201

    # Sion
    login_user_via_session(client, librarian_sion_no_email.user)

    res = client.post(
        post_url,
        data=json.dumps(holding_lib_martigny_data),
        headers=json_header
    )
    assert res.status_code == 403


def test_holding_secure_api_update(client, holding_lib_sion,
                                   librarian_martigny_no_email,
                                   librarian_sion_no_email,
                                   holding_lib_sion_data,
                                   json_header):
    """Test holding secure api update."""
    # Martigny
    login_user_via_session(client, librarian_martigny_no_email.user)
    record_url = url_for('invenio_records_rest.hold_item',
                         pid_value=holding_lib_sion.pid)

    data = holding_lib_sion_data
    data['call_number'] = 'call_number'
    res = client.put(
        record_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 403

    # Sion
    login_user_via_session(client, librarian_sion_no_email.user)

    res = client.put(
        record_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 200


def test_holding_secure_api_delete(client, holding_lib_saxon,
                                   librarian_martigny_no_email,
                                   librarian_sion_no_email):
    """Test holding secure api delete."""
    login_user_via_session(client, librarian_martigny_no_email.user)
    record_url = url_for('invenio_records_rest.hold_item',
                         pid_value=holding_lib_saxon.pid)
    # Martigny
    res = client.delete(record_url)
    assert res.status_code == 204

    # Sion
    login_user_via_session(client, librarian_sion_no_email.user)

    res = client.delete(record_url)
    assert res.status_code == 410
