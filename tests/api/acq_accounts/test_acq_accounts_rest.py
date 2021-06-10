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

"""Tests REST API acquisition accounts."""

import json

import mock
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import VerifyRecordPermissionPatch, get_json, postdata, \
    to_relative_url


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_acq_accounts_library_facets(
    client, org_martigny, acq_account_fiction_martigny, rero_json_header
):
    """Test record retrieval."""
    list_url = url_for('invenio_records_rest.acac_list', view='org1')

    res = client.get(list_url, headers=rero_json_header)
    data = get_json(res)
    aggs = data['aggregations']
    assert 'library' in aggs


def test_acq_accounts_permissions(client, acq_account_fiction_martigny,
                                  json_header):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.acac_item', pid_value='acac1')

    res = client.get(item_url)
    assert res.status_code == 401

    res, _ = postdata(
        client,
        'invenio_records_rest.acac_list',
        {}
    )
    assert res.status_code == 401

    res = client.put(
        url_for('invenio_records_rest.acac_item', pid_value='acac1'),
        data={},
        headers=json_header
    )

    res = client.delete(item_url)
    assert res.status_code == 401


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_acq_accounts_get(client, acq_account_fiction_martigny):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.acac_item', pid_value='acac1')
    acq_account = acq_account_fiction_martigny
    res = client.get(item_url)
    assert res.status_code == 200

    assert res.headers['ETag'] == '"{}"'.format(acq_account.revision_id)

    data = get_json(res)
    assert acq_account.dumps() == data['metadata']

    # Check metadata
    for k in ['created', 'updated', 'metadata', 'links']:
        assert k in data

    # Check self links
    res = client.get(to_relative_url(data['links']['self']))
    assert res.status_code == 200
    assert data == get_json(res)
    assert acq_account.dumps() == data['metadata']

    list_url = url_for('invenio_records_rest.acac_list', pid='acac1')
    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)

    assert data['hits']['hits'][0]['metadata'] == acq_account.replace_refs()


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_acq_accounts_post_put_delete(client,
                                      lib_saxon,
                                      acq_account_books_saxon_data,
                                      budget_2020_martigny,
                                      json_header):
    """Test record retrieval."""
    # Create record / POST
    item_url = url_for('invenio_records_rest.acac_item', pid_value='1')
    list_url = url_for('invenio_records_rest.acac_list', q='pid:1')

    acq_account_books_saxon_data.pop('pid')
    res, data = postdata(
        client,
        'invenio_records_rest.acac_list',
        acq_account_books_saxon_data
    )
    assert res.status_code == 201

    # Check that the returned record matches the given data
    acq_account_books_saxon_data['pid'] = '1'
    acq_account_books_saxon_data['organisation'] = {
        '$ref': 'https://bib.rero.ch/api/organisations/org1'
    }
    assert data['metadata'] == acq_account_books_saxon_data

    res = client.get(item_url)
    assert res.status_code == 200
    data = get_json(res)
    assert acq_account_books_saxon_data == data['metadata']

    # Update record/PUT
    acq_account_books_saxon_data['name'] = 'Test Name'
    res = client.put(
        item_url,
        data=json.dumps(acq_account_books_saxon_data),
        headers=json_header
    )
    assert res.status_code == 200
    # assert res.headers['ETag'] != '"{}"'.format(librarie.revision_id)

    # Check that the returned record matches the given data
    data = get_json(res)
    assert data['metadata']['name'] == 'Test Name'

    res = client.get(item_url)
    assert res.status_code == 200

    data = get_json(res)
    assert data['metadata']['name'] == 'Test Name'

    res = client.get(list_url)
    assert res.status_code == 200

    data = get_json(res)['hits']['hits'][0]
    assert data['metadata']['name'] == 'Test Name'

    # Delete record/DELETE
    res = client.delete(item_url)
    assert res.status_code == 204

    res = client.get(item_url)
    assert res.status_code == 410


def test_acq_accounts_can_delete(
        client, document, acq_account_fiction_martigny,
        acq_order_line_fiction_martigny, acq_order_fiction_martigny):
    """Test can delete an acq account."""
    can, reasons = acq_account_fiction_martigny.can_delete
    assert not can
    assert reasons['links']['acq_order_lines']


def test_filtered_acq_accounts_get(
        client, librarian_martigny, acq_account_fiction_martigny,
        librarian_sion, acq_account_fiction_sion):
    """Test acq accounts filter by organisation."""
    list_url = url_for('invenio_records_rest.acac_list')

    res = client.get(list_url)
    assert res.status_code == 401

    # Martigny
    login_user_via_session(client, librarian_martigny.user)
    list_url = url_for('invenio_records_rest.acac_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total']['value'] == 1

    # Sion
    login_user_via_session(client, librarian_sion.user)
    list_url = url_for('invenio_records_rest.acac_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total']['value'] == 1


def test_acq_account_secure_api(client, json_header,
                                acq_account_fiction_martigny,
                                librarian_martigny,
                                librarian_sion):
    """Test acq account secure api access."""
    # Martigny
    login_user_via_session(client, librarian_martigny.user)
    record_url = url_for('invenio_records_rest.acac_item',
                         pid_value=acq_account_fiction_martigny.pid)

    res = client.get(record_url)
    assert res.status_code == 200

    # Sion
    login_user_via_session(client, librarian_sion.user)
    record_url = url_for('invenio_records_rest.acac_item',
                         pid_value=acq_account_fiction_martigny.pid)

    res = client.get(record_url)
    assert res.status_code == 403


def test_acq_account_secure_api_create(client, json_header,
                                       acq_account_fiction_martigny_data,
                                       librarian_martigny,
                                       librarian_sion,
                                       acq_account_books_saxon_data,
                                       system_librarian_martigny):
    """Test acq account secure api create."""
    # Martigny
    login_user_via_session(client, librarian_martigny.user)
    post_entrypoint = 'invenio_records_rest.acac_list'

    acq_account_books_saxon_data.pop('pid')
    res, _ = postdata(
        client,
        post_entrypoint,
        acq_account_books_saxon_data
    )
    assert res.status_code == 403

    acq_account_fiction_martigny_data.pop('pid')
    res, _ = postdata(
        client,
        post_entrypoint,
        acq_account_fiction_martigny_data
    )
    assert res.status_code == 201

    login_user_via_session(client, system_librarian_martigny.user)
    res, _ = postdata(
        client,
        post_entrypoint,
        acq_account_fiction_martigny_data
    )
    assert res.status_code == 201

    # Sion
    login_user_via_session(client, librarian_sion.user)

    res, _ = postdata(
        client,
        post_entrypoint,
        acq_account_books_saxon_data
    )
    assert res.status_code == 403


def test_acq_account_secure_api_update(client,
                                       acq_account_books_martigny,
                                       librarian_martigny,
                                       librarian_sion,
                                       acq_account_books_martigny_data,
                                       json_header):
    """Test acq account secure api update."""
    # Martigny
    login_user_via_session(client, librarian_martigny.user)
    record_url = url_for('invenio_records_rest.acac_item',
                         pid_value=acq_account_books_martigny.pid)

    data = acq_account_books_martigny
    data['name'] = 'Test Name'
    res = client.put(
        record_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 200

    # Sion
    login_user_via_session(client, librarian_sion.user)

    res = client.put(
        record_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 403


def test_acq_account_secure_api_delete(client,
                                       acq_account_books_martigny,
                                       librarian_martigny,
                                       librarian_sion,
                                       acq_account_general_fully,
                                       json_header):
    """Test acq account secure api delete."""
    # Martigny
    login_user_via_session(client, librarian_martigny.user)
    record_url = url_for('invenio_records_rest.acac_item',
                         pid_value=acq_account_books_martigny.pid)

    res = client.delete(record_url)
    assert res.status_code == 204

    record_url = url_for('invenio_records_rest.acac_item',
                         pid_value=acq_account_general_fully.pid)

    res = client.delete(record_url)
    assert res.status_code == 403

    # Sion
    login_user_via_session(client, librarian_sion.user)

    res = client.delete(record_url)
    assert res.status_code == 403
