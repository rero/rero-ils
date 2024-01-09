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

"""Tests REST API libraries."""

import json
from datetime import datetime, timedelta

import mock
import pytest
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import VerifyRecordPermissionPatch, get_json, postdata, \
    to_relative_url

from rero_ils.modules.libraries.api import LibraryNeverOpen


def test_libraries_permissions(client, lib_martigny, json_header):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.lib_item', pid_value='lib1')

    res = client.get(item_url)
    assert res.status_code == 401

    res, _ = postdata(client, 'invenio_records_rest.lib_list', {})
    assert res.status_code == 401

    client.put(item_url, data={}, headers=json_header)
    res = client.delete(item_url)
    assert res.status_code == 401


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_libraries_get(client, lib_martigny):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.lib_item', pid_value='lib1')
    list_url = url_for('invenio_records_rest.lib_list', q='pid:lib1')

    res = client.get(item_url)
    assert res.status_code == 200
    assert res.headers['ETag'] == f'"{lib_martigny.revision_id}"'

    data = get_json(res)
    assert lib_martigny.dumps() == data['metadata']

    # Check metadata
    for k in ['created', 'updated', 'metadata', 'links']:
        assert k in data

    # Check self links
    res = client.get(to_relative_url(data['links']['self']))
    assert res.status_code == 200
    assert data == get_json(res)
    assert lib_martigny.dumps() == data['metadata']

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)

    assert data['hits']['hits'][0]['metadata'] == lib_martigny.replace_refs()


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_libraries_post_put_delete(client, lib_martigny_data, json_header):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.lib_item', pid_value='1')
    list_url = url_for('invenio_records_rest.lib_list', q='pid:1')

    # Create record / POST
    lib_martigny_data['pid'] = '1'
    res, data = postdata(
        client,
        'invenio_records_rest.lib_list',
        lib_martigny_data
    )

    assert res.status_code == 201

    # Check that the returned record matches the given data
    assert data['metadata'] == lib_martigny_data

    res = client.get(item_url)
    assert res.status_code == 200
    data = get_json(res)
    assert lib_martigny_data == data['metadata']

    # Update record/PUT
    data = lib_martigny_data
    data['name'] = 'Test Name'
    res = client.put(
        item_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 200
    # assert res.headers['ETag'] != f'"{librarie.revision_id}"'

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


def test_non_circulating_libraries(
        lib_sion, lib_martigny, lib_martigny_bourg, loc_public_martigny,
        loc_public_martigny_bourg):
    """Test pickup vs transaction locations."""
    assert not lib_sion.get_pickup_location_pid()
    assert not lib_martigny_bourg.get_pickup_location_pid()
    assert lib_martigny.get_pickup_location_pid()
    assert lib_martigny_bourg.get_transaction_location_pid()


def test_library_never_open(lib_sion):
    """Test library with no opening hours."""
    assert lib_sion._has_is_open()
    assert lib_sion.next_open()

    del lib_sion['opening_hours']
    # add an exception date in the past
    open_exception = {
        'is_open': True,
        'start_date': '2012-01-09',
        'title': 'Ouverture exceptionnelle',
        'times': [
            {
                'end_time': '16:00',
                'start_time': '12:00'
            }
        ]
    }

    lib_sion['exception_dates'].append(open_exception)
    lib_sion.update(lib_sion, dbcommit=True, reindex=True)

    # check that the exception in the past is not considered for next open date
    with pytest.raises(LibraryNeverOpen):
        assert lib_sion.next_open()

    # compute a date in the future and add it as exception date
    today = datetime.today()
    future_date = (today + timedelta(days=14)).strftime('%Y-%m-%d')
    open_exception['start_date'] = future_date
    lib_sion.update(lib_sion, dbcommit=True, reindex=True)

    # check that the exception in the future is considered as open date
    assert lib_sion._has_is_open()

    del lib_sion['exception_dates']
    lib_sion.update(lib_sion, dbcommit=True, reindex=True)

    with pytest.raises(LibraryNeverOpen):
        assert lib_sion.next_open()


def test_library_can_delete(lib_martigny, librarian_martigny,
                            loc_public_martigny, acq_receipt_fiction_martigny):
    """Test can delete a library."""
    can, reasons = lib_martigny.can_delete
    assert not can
    assert reasons['links']['locations']
    assert reasons['links']['patrons']
    assert reasons['links']['acq_receipts']


def test_filtered_libraries_get(
        client, librarian_martigny, lib_martigny, lib_saxon,
        lib_fully, librarian_sion, lib_sion):
    """Test libraries filter by organisation."""    # Martigny
    login_user_via_session(client, librarian_martigny.user)
    list_url = url_for('invenio_records_rest.lib_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total']['value'] == 4

    # Sion
    login_user_via_session(client, librarian_sion.user)
    list_url = url_for('invenio_records_rest.lib_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total']['value'] == 1


def test_library_secure_api(client, lib_martigny, lib_fully,
                            librarian_martigny,
                            librarian_sion,
                            system_librarian_martigny,
                            system_librarian_sion):
    """Test library secure api access."""
    # Martigny
    login_user_via_session(client, librarian_martigny.user)
    record_url = url_for('invenio_records_rest.lib_item',
                         pid_value=lib_martigny.pid)

    res = client.get(record_url)
    # a librarian is authorized to access its library record of its org
    assert res.status_code == 200

    record_url = url_for('invenio_records_rest.lib_item',
                         pid_value=lib_fully.pid)
    res = client.get(record_url)
    # a librarian is authorized to access other library records of its org
    assert res.status_code == 200

    login_user_via_session(client, system_librarian_martigny.user)
    record_url = url_for('invenio_records_rest.lib_item',
                         pid_value=lib_martigny.pid)
    res = client.get(record_url)
    # a sys_lib is authorized to access its library record of its org
    assert res.status_code == 200

    record_url = url_for('invenio_records_rest.lib_item',
                         pid_value=lib_fully.pid)
    res = client.get(record_url)
    # a sys_lib is authorized to access libraries  of its org
    assert res.status_code == 200

    # Sion
    login_user_via_session(client, librarian_sion.user)
    record_url = url_for('invenio_records_rest.lib_item',
                         pid_value=lib_martigny.pid)

    res = client.get(record_url)
    # a librarian is not authorized to access library record of another  org
    assert res.status_code == 403

    login_user_via_session(client, system_librarian_sion.user)
    res = client.get(record_url)
    # a sys_lib is not authorized to access its library record of its org
    assert res.status_code == 403


def test_library_secure_api_create(client, lib_martigny,
                                   lib_fully_data, librarian2_martigny,
                                   librarian_sion,
                                   lib_martigny_data,
                                   system_librarian_martigny,
                                   system_librarian_sion):
    """Test library secure api create."""
    # Martigny
    login_user_via_session(client, librarian2_martigny.user)
    post_entrypoint = 'invenio_records_rest.lib_list'

    del lib_martigny_data['pid']
    res, _ = postdata(client, post_entrypoint, lib_martigny_data)
    # a not library manager is not authorized to create its library record
    assert res.status_code == 403

    del lib_fully_data['pid']
    res, _ = postdata(client, post_entrypoint, lib_fully_data)
    # a not library manager is not authorized to create library record
    assert res.status_code == 403

    # * sys_librarian is authorized to create its library record of its org
    # * sys_librarian is authorized to create new library record in its org
    login_user_via_session(client, system_librarian_martigny.user)
    res, _ = postdata(client, post_entrypoint, lib_martigny_data)
    assert res.status_code == 201
    res, _ = postdata(client, post_entrypoint, lib_fully_data)
    assert res.status_code == 201


def test_library_secure_api_update(client, lib_fully, lib_martigny,
                                   librarian_martigny,
                                   librarian_sion,
                                   json_header,
                                   system_librarian_martigny,
                                   system_librarian_sion):
    """Test library secure api update."""
    # Martigny
    login_user_via_session(client, librarian_martigny.user)
    record_url = url_for('invenio_records_rest.lib_item',
                         pid_value=lib_martigny.pid)

    lib_martigny['name'] = 'New Name'
    res = client.put(
        record_url,
        data=json.dumps(lib_martigny),
        headers=json_header
    )
    # a librarian is authorized to update its library in its org
    assert res.status_code == 200

    record_url = url_for('invenio_records_rest.lib_item',
                         pid_value=lib_fully.pid)

    lib_fully['name'] = 'New Name'
    res = client.put(
        record_url,
        data=json.dumps(lib_fully),
        headers=json_header
    )
    # a librarian is not authorized to update an external library of its org
    assert res.status_code == 403

    login_user_via_session(client, system_librarian_martigny.user)
    res = client.put(
        record_url,
        data=json.dumps(lib_fully),
        headers=json_header
    )
    # a sys_librarian is authorized to update any library of its org
    assert res.status_code == 200

    record_url = url_for('invenio_records_rest.lib_item',
                         pid_value=lib_martigny.pid)
    lib_martigny['name'] = 'New Name 2'
    res = client.put(
        record_url,
        data=json.dumps(lib_martigny),
        headers=json_header
    )
    # a sys_librarian is authorized to update any library of its org
    assert res.status_code == 200

    # Sion
    login_user_via_session(client, librarian_sion.user)

    record_url = url_for('invenio_records_rest.lib_item',
                         pid_value=lib_fully.pid)

    lib_fully['name'] = 'New Name 2'
    res = client.put(
        record_url,
        data=json.dumps(lib_fully),
        headers=json_header
    )
    # librarian is not authorized to update an external library of another org
    assert res.status_code == 403

    login_user_via_session(client, system_librarian_sion.user)
    res = client.put(
        record_url,
        data=json.dumps(lib_fully),
        headers=json_header
    )
    # sys_lib is not authorized to update an external library of another org
    assert res.status_code == 403


def test_library_secure_api_delete(client, lib_fully, lib_martigny,
                                   librarian2_martigny,
                                   librarian_sion,
                                   system_librarian_martigny,
                                   system_librarian_sion):
    """Test library secure api delete."""
    # Martigny
    login_user_via_session(client, librarian2_martigny.user)
    record_url = url_for('invenio_records_rest.lib_item',
                         pid_value=lib_martigny.pid)

    res = client.delete(record_url)
    # librarian is not authorized to delete its library of its org
    assert res.status_code == 403

    record_url = url_for('invenio_records_rest.lib_item',
                         pid_value=lib_fully.pid)

    res = client.delete(record_url)
    # librarian is not authorized to delete an external library of its org
    assert res.status_code == 403

    # Sion
    login_user_via_session(client, librarian_sion.user)

    res = client.delete(record_url)
    # librarian is not authorized to delete an external library of another org
    assert res.status_code == 403

    login_user_via_session(client, system_librarian_martigny.user)

    res = client.delete(record_url)
    # sys_librarian is authorized to delete any library of its org
    assert res.status_code == 204

    login_user_via_session(client, system_librarian_sion.user)
    record_url = url_for('invenio_records_rest.lib_item',
                         pid_value=lib_martigny.pid)

    res = client.delete(record_url)
    # sys_librarian is not authorized to delete any library of other org
    assert res.status_code == 403
