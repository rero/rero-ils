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

"""Tests REST API locations."""

import json
from copy import deepcopy

import mock
import pytest
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import VerifyRecordPermissionPatch, get_json, postdata, \
    to_relative_url

from rero_ils.modules.errors import RecordValidationError


def test_locations_permissions(client, loc_public_martigny, json_header):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.loc_item', pid_value='loc1')

    res = client.get(item_url)
    assert res.status_code == 401

    res, _ = postdata(
        client,
        'invenio_records_rest.loc_list',
        {}
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
def test_locations_get(client, loc_public_martigny):
    """Test record retrieval."""
    location = loc_public_martigny
    item_url = url_for('invenio_records_rest.loc_item', pid_value=location.pid)
    list_url = url_for(
        'invenio_records_rest.loc_list', q='pid:' + location.pid)
    item_url_with_resolve = url_for(
        'invenio_records_rest.loc_item',
        pid_value=location.pid,
        resolve=1,
        sources=1
    )

    res = client.get(item_url)
    assert res.status_code == 200

    assert res.headers['ETag'] == '"{}"'.format(location.revision_id)

    data = get_json(res)
    assert location.dumps() == data['metadata']

    # Check metadata
    for k in ['created', 'updated', 'metadata', 'links']:
        assert k in data

    # Check self links
    res = client.get(to_relative_url(data['links']['self']))
    assert res.status_code == 200
    assert data == get_json(res)
    assert location.dumps() == data['metadata']

    # check resolve
    res = client.get(item_url_with_resolve)
    assert res.status_code == 200
    data = get_json(res)
    assert location.replace_refs().dumps() == data['metadata']

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    result = data['hits']['hits'][0]['metadata']
    # organisation has been added during the indexing
    del(result['organisation'])
    assert result == location.replace_refs()


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_locations_post_put_delete(client, lib_martigny,
                                   loc_public_martigny_data,
                                   json_header):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.loc_item', pid_value='1')
    list_url = url_for('invenio_records_rest.loc_list', q='pid:1')
    location_data = loc_public_martigny_data
    # Create record / POST
    location_data['pid'] = '1'
    res, data = postdata(
        client,
        'invenio_records_rest.loc_list',
        location_data
    )
    assert res.status_code == 201

    # Check that the returned record matches the given data
    assert data['metadata'] == location_data

    res = client.get(item_url)
    assert res.status_code == 200
    data = get_json(res)
    assert location_data == data['metadata']

    # Update record/PUT
    data = location_data
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


def test_location_can_delete(client, item_lib_martigny, loc_public_martigny):
    """Test can delete a location."""
    links = loc_public_martigny.get_links_to_me()
    assert 'items' in links

    assert not loc_public_martigny.can_delete

    reasons = loc_public_martigny.reasons_not_to_delete()
    assert 'links' in reasons


def test_filtered_locations_get(
        client, librarian_martigny_no_email, loc_public_martigny,
        loc_restricted_martigny, loc_public_saxon, loc_restricted_saxon,
        loc_public_fully, loc_restricted_fully,
        librarian_sion_no_email,
        loc_public_sion, loc_restricted_sion
):
    """Test location filter by organisation."""
    # Martigny
    login_user_via_session(client, librarian_martigny_no_email.user)
    list_url = url_for('invenio_records_rest.loc_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total'] == 6

    # Sion
    login_user_via_session(client, librarian_sion_no_email.user)
    list_url = url_for('invenio_records_rest.loc_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total'] == 2


def test_location_secure_api(client, json_header, loc_public_martigny,
                             loc_public_fully, librarian_martigny_no_email,
                             librarian_sion_no_email,
                             system_librarian_martigny_no_email,
                             system_librarian_sion_no_email):
    """Test location secure api access."""
    # Martigny
    login_user_via_session(client, librarian_martigny_no_email.user)
    record_url = url_for('invenio_records_rest.loc_item',
                         pid_value=loc_public_martigny.pid)

    res = client.get(record_url)
    # a librarian is authorized to access any location of its library
    assert res.status_code == 200

    record_url = url_for('invenio_records_rest.loc_item',
                         pid_value=loc_public_fully.pid)

    res = client.get(record_url)
    # a librarian is authorized to access any location of its organisation
    assert res.status_code == 200

    login_user_via_session(client, system_librarian_martigny_no_email.user)
    res = client.get(record_url)
    # a sys_librarian is authorized to access any location of its organisation
    assert res.status_code == 200

    # Sion
    login_user_via_session(client, librarian_sion_no_email.user)
    record_url = url_for('invenio_records_rest.loc_item',
                         pid_value=loc_public_martigny.pid)

    res = client.get(record_url)
    # librarian is not authorized to access any location of other organisation
    assert res.status_code == 403

    login_user_via_session(client, system_librarian_sion_no_email.user)
    res = client.get(record_url)
    # a sys_librarian is not authorized to access any location of other org
    assert res.status_code == 403


def test_location_secure_api_create(client, lib_fully, lib_martigny,
                                    librarian_martigny_no_email,
                                    librarian_sion_no_email,
                                    loc_public_martigny_data,
                                    loc_public_fully_data,
                                    system_librarian_martigny_no_email,
                                    system_librarian_sion_no_email):
    """Test location secure api create."""
    # try to create a pickup location without pickup location name. This should
    # be failed due to `extended_validation` rules
    login_user_via_session(client, librarian_martigny_no_email.user)
    post_entrypoint = 'invenio_records_rest.loc_list'
    fake_location_data = deepcopy(loc_public_martigny_data)
    del fake_location_data['pid']
    if 'pickup_name' in fake_location_data:
        del fake_location_data['pickup_name']
    fake_location_data['is_pickup'] = True
    with pytest.raises(RecordValidationError):
        res, _ = postdata(
            client,
            post_entrypoint,
            fake_location_data
        )

    # Martigny
    del loc_public_martigny_data['pid']
    res, _ = postdata(
        client,
        post_entrypoint,
        loc_public_martigny_data
    )
    # librarian is authorized to create a location in its library.
    assert res.status_code == 201

    del loc_public_fully_data['pid']
    res, _ = postdata(
        client,
        post_entrypoint,
        loc_public_fully_data
    )
    # librarian is not authorized to create a location in other libraries.
    assert res.status_code == 403

    login_user_via_session(client, system_librarian_martigny_no_email.user)
    res, _ = postdata(
        client,
        post_entrypoint,
        loc_public_fully_data
    )
    # sys_librarian is authorized to create any location in its org.
    assert res.status_code == 201

    # Sion
    login_user_via_session(client, librarian_sion_no_email.user)

    res, _ = postdata(
        client,
        post_entrypoint,
        loc_public_martigny_data
    )
    # librarian is not authorized to create a location at other org.
    assert res.status_code == 403

    login_user_via_session(client, system_librarian_sion_no_email.user)
    res, _ = postdata(
        client,
        post_entrypoint,
        loc_public_martigny_data
    )
    # sys_librarian is authorized to create a location in other org.
    assert res.status_code == 403


def test_location_secure_api_update(client, loc_restricted_saxon,
                                    loc_public_fully, loc_public_martigny,
                                    librarian_martigny_no_email,
                                    librarian_sion_no_email,
                                    json_header,
                                    system_librarian_martigny_no_email,
                                    system_librarian_sion_no_email):
    """Test location secure api update."""
    # Martigny
    login_user_via_session(client, librarian_martigny_no_email.user)
    record_url = url_for('invenio_records_rest.loc_item',
                         pid_value=loc_public_martigny.pid)

    loc_public_martigny['name'] = 'New Name'
    res = client.put(
        record_url,
        data=json.dumps(loc_public_martigny),
        headers=json_header
    )
    # librarian is authorized to update a location in its library.
    assert res.status_code == 200

    record_url = url_for('invenio_records_rest.loc_item',
                         pid_value=loc_restricted_saxon.pid)

    loc_restricted_saxon['name'] = 'New Name'
    res = client.put(
        record_url,
        data=json.dumps(loc_restricted_saxon),
        headers=json_header
    )
    # librarian is not authorized to update a location of another library.
    assert res.status_code == 403

    login_user_via_session(client, system_librarian_martigny_no_email.user)
    res = client.put(
        record_url,
        data=json.dumps(loc_restricted_saxon),
        headers=json_header
    )
    # sys_librarian is authorized to update any location of its org.
    assert res.status_code == 200

    # Sion
    login_user_via_session(client, librarian_sion_no_email.user)

    res = client.put(
        record_url,
        data=json.dumps(loc_restricted_saxon),
        headers=json_header
    )
    # librarian is not authorized to update any location of another org.
    assert res.status_code == 403

    login_user_via_session(client, system_librarian_sion_no_email.user)
    res = client.put(
        record_url,
        data=json.dumps(loc_restricted_saxon),
        headers=json_header
    )
    assert res.status_code == 403


def test_location_secure_api_delete(client, loc_restricted_saxon,
                                    loc_restricted_martigny,
                                    loc_public_martigny,
                                    librarian_martigny_no_email,
                                    librarian_sion_no_email,
                                    system_librarian_martigny_no_email,
                                    system_librarian_sion_no_email):
    """Test location secure api delete."""

    login_user_via_session(client, librarian_martigny_no_email.user)
    record_url = url_for('invenio_records_rest.loc_item',
                         pid_value=loc_restricted_martigny.pid)

    res = client.delete(record_url)
    # librarian is authorized to delete any location of its library.
    assert res.status_code == 204

    record_url = url_for('invenio_records_rest.loc_item',
                         pid_value=loc_restricted_saxon.pid)

    res = client.delete(record_url)
    # librarian is not authorized to delete any location of other libraries.
    assert res.status_code == 403

    login_user_via_session(client, system_librarian_martigny_no_email.user)
    res = client.delete(record_url)
    # librarian is authorized to delete any location of its org.
    assert res.status_code == 204

    # Sion
    login_user_via_session(client, librarian_sion_no_email.user)

    record_url = url_for('invenio_records_rest.loc_item',
                         pid_value=loc_public_martigny.pid)
    res = client.delete(record_url)
    # librarian is not authorized to delete any location of other org.
    assert res.status_code == 403

    login_user_via_session(client, system_librarian_sion_no_email.user)
    res = client.delete(record_url)
    # sys_ibrarian is not authorized to delete any location of other org.
    assert res.status_code == 403
