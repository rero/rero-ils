#
# This file is part of RERO ILS.
# Copyright (C) 2017 RERO.
#
# RERO ILS is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# RERO ILS is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RERO ILS; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Tests REST API libraries."""

import json

import mock
import pytest
from dateutil import parser
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import VerifyRecordPermissionPatch, get_json, to_relative_url

from rero_ils.modules.libraries.api import Library, LibraryNeverOpen


def test_libraries_permissions(client, lib_martigny, json_header):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.lib_item', pid_value='lib1')
    post_url = url_for('invenio_records_rest.lib_list')

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
def test_libraries_get(client, lib_martigny):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.lib_item', pid_value='lib1')
    list_url = url_for('invenio_records_rest.lib_list', q='pid:lib1')

    res = client.get(item_url)
    assert res.status_code == 200

    assert res.headers['ETag'] == '"{}"'.format(lib_martigny.revision_id)

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
    post_url = url_for('invenio_records_rest.lib_list')
    list_url = url_for('invenio_records_rest.lib_list', q='pid:1')

    # Create record / POST
    lib_martigny_data['pid'] = '1'
    res = client.post(
        post_url,
        data=json.dumps(lib_martigny_data),
        headers=json_header
    )

    assert res.status_code == 201

    # Check that the returned record matches the given data
    data = get_json(res)
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


def test_library_no_pickup(lib_sion):
    """Test library with no pick_up location."""
    assert not lib_sion.get_pickup_location_pid()


def test_library_never_open(lib_sion):
    """Test library with no opening hours."""
    assert lib_sion._has_is_open()
    assert lib_sion.next_open()

    del lib_sion['opening_hours']
    lib_sion.update(lib_sion, dbcommit=True, reindex=True)

    assert lib_sion._has_is_open()

    del lib_sion['exception_dates']
    lib_sion.update(lib_sion, dbcommit=True, reindex=True)

    with pytest.raises(LibraryNeverOpen):
        assert lib_sion.next_open()


def test_library_exceptions(lib_martigny):
    """Test library exceptions."""
    assert lib_martigny._has_is_open()
    assert lib_martigny.next_open()
    assert lib_martigny.is_open(date=parser.parse('2018-12-15'))
    assert lib_martigny.is_open(date=parser.parse('2019-01-05'))
    assert not lib_martigny.is_open(date=parser.parse('2019-08-01'))

    exception_dates = lib_martigny.get('exception_dates')
    exception_open_false = lib_martigny._has_exception(
        _open=False,
        date=parser.parse('2019-01-06'),
        exception_dates=exception_dates,
        day_only=False
    )
    exception_open_true = lib_martigny._has_exception(
        _open=True,
        date=parser.parse('2019-01-06'),
        exception_dates=exception_dates,
        day_only=False
    )

    assert exception_open_false
    assert not exception_open_true

    assert not lib_martigny._has_exception(
        _open=True,
        date=parser.parse('2019-08-01'),
        exception_dates=exception_dates,
        day_only=False
    )


def test_library_can_delete(lib_martigny, librarian_martigny_no_email,
                            loc_public_martigny):
    """Test can delete a library."""
    links = lib_martigny.get_links_to_me()
    assert 'locations' in links
    assert 'patrons' in links

    assert not lib_martigny.can_delete

    reasons = lib_martigny.reasons_not_to_delete()
    assert 'links' in reasons


def test_filtered_libraries_get(
        client, librarian_martigny_no_email, lib_martigny, lib_saxon,
        lib_fully, librarian_sion_no_email, lib_sion):
    """Test libraries filter by organisation."""    # Martigny
    login_user_via_session(client, librarian_martigny_no_email.user)
    list_url = url_for('invenio_records_rest.lib_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total'] == 3

    # Sion
    login_user_via_session(client, librarian_sion_no_email.user)
    list_url = url_for('invenio_records_rest.lib_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total'] == 1


def test_library_secure_api(client, lib_martigny,
                            librarian_martigny_no_email,
                            librarian_sion_no_email):
    """Test library secure api access."""
    # Martigny
    login_user_via_session(client, librarian_martigny_no_email.user)
    record_url = url_for('invenio_records_rest.lib_item',
                         pid_value=lib_martigny.pid)

    res = client.get(record_url)
    assert res.status_code == 200

    # Sion
    login_user_via_session(client, librarian_sion_no_email.user)
    record_url = url_for('invenio_records_rest.lib_item',
                         pid_value=lib_martigny.pid)

    res = client.get(record_url)
    assert res.status_code == 403


def test_library_secure_api_create(client, json_header, lib_martigny,
                                   librarian_martigny_no_email,
                                   librarian_sion_no_email,
                                   lib_martigny_data):
    """Test library secure api create."""
    # Martigny
    login_user_via_session(client, librarian_martigny_no_email.user)
    post_url = url_for('invenio_records_rest.lib_list')

    del lib_martigny_data['pid']
    res = client.post(
        post_url,
        data=json.dumps(lib_martigny_data),
        headers=json_header
    )
    assert res.status_code == 201

    # Sion
    login_user_via_session(client, librarian_sion_no_email.user)

    res = client.post(
        post_url,
        data=json.dumps(lib_martigny_data),
        headers=json_header
    )
    assert res.status_code == 403


def test_library_secure_api_update(client, lib_fully,
                                   librarian_martigny_no_email,
                                   librarian_sion_no_email,
                                   lib_fully_data,
                                   json_header):
    """Test library secure api update."""
    # Martigny
    login_user_via_session(client, librarian_martigny_no_email.user)
    record_url = url_for('invenio_records_rest.lib_item',
                         pid_value=lib_fully.pid)

    data = lib_fully_data
    data['name'] = 'New Name'
    res = client.put(
        record_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 200

    # Sion
    login_user_via_session(client, librarian_sion_no_email.user)

    res = client.put(
        record_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 403


def test_library_secure_api_delete(client, lib_fully,
                                   librarian_martigny_no_email,
                                   librarian_sion_no_email):
    """Test library secure api delete."""
    # Martigny
    login_user_via_session(client, librarian_martigny_no_email.user)
    record_url = url_for('invenio_records_rest.lib_item',
                         pid_value=lib_fully.pid)

    res = client.delete(record_url)
    assert res.status_code == 204

    # Sion
    login_user_via_session(client, librarian_sion_no_email.user)

    res = client.delete(record_url)
    assert res.status_code == 410
