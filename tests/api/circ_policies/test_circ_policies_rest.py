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

"""Tests REST API for circulation policies."""

import json

import mock
import pytest
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import VerifyRecordPermissionPatch, get_json, postdata, \
    to_relative_url

from rero_ils.modules.api import IlsRecordError


def test_circ_policies_permissions(
        client, circ_policy_default_martigny, json_header):
    """Test policy retrieval."""
    item_url = url_for('invenio_records_rest.cipo_item', pid_value='cipo1')

    res = client.get(item_url)
    assert res.status_code == 401

    res, _ = postdata(
        client,
        'invenio_records_rest.cipo_list',
        {}
    )
    assert res.status_code == 401

    res = client.put(
        url_for('invenio_records_rest.cipo_item', pid_value='cipo1'),
        data={},
        headers=json_header
    )

    res = client.delete(item_url)
    assert res.status_code == 401

    res = client.get(url_for('circ_policies.name_validate', name='standard'))
    assert res.status_code == 401


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_circ_policies_get(client, circ_policy_default_martigny):
    """Test policy retrieval."""
    circ_policy = circ_policy_default_martigny
    item_url = url_for('invenio_records_rest.cipo_item', pid_value='cipo1')

    res = client.get(item_url)
    assert res.status_code == 200

    assert res.headers['ETag'] == '"{}"'.format(circ_policy.revision_id)

    data = get_json(res)
    assert circ_policy.dumps() == data['metadata']

    # Check metadata
    for k in ['created', 'updated', 'metadata', 'links']:
        assert k in data

    # Check self links
    res = client.get(to_relative_url(data['links']['self']))
    assert res.status_code == 200
    json = get_json(res)
    assert data == json
    assert circ_policy.dumps() == data['metadata']

    list_url = url_for('invenio_records_rest.cipo_list', pid='cipo1')
    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)

    assert data['hits']['hits'][0]['metadata'] == circ_policy.replace_refs()


def test_filtered_circ_policies_get(
        client, librarian_martigny, circ_policy_default_martigny,
        circ_policy_short_martigny, circ_policy_temp_martigny,
        librarian_sion, circ_policy_default_sion):
    """Test circulation policies filter by organisation."""
    # Martigny
    login_user_via_session(client, librarian_martigny.user)
    list_url = url_for('invenio_records_rest.cipo_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total']['value'] == 3

    # Sion
    login_user_via_session(client, librarian_sion.user)
    list_url = url_for('invenio_records_rest.cipo_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total']['value'] == 1


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_circ_policies_post_put_delete(client, org_martigny,
                                       circ_policy_default_martigny_data,
                                       json_header):
    """Test policy retrieval."""
    # Create policy / POST
    item_url = url_for('invenio_records_rest.cipo_item', pid_value='1')
    list_url = url_for('invenio_records_rest.cipo_list', q='pid:1')
    del circ_policy_default_martigny_data['pid']
    res, data = postdata(
        client,
        'invenio_records_rest.cipo_list',
        circ_policy_default_martigny_data
    )
    assert res.status_code == 201

    # Check that the returned policy matches the given data
    circ_policy_default_martigny_data['pid'] = '1'

    assert data['metadata'] == circ_policy_default_martigny_data

    res = client.get(item_url)
    assert res.status_code == 200
    data = get_json(res)
    assert circ_policy_default_martigny_data == data['metadata']

    # Update policy/PUT
    data = circ_policy_default_martigny_data
    data['name'] = 'Test Name'
    res = client.put(
        item_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 200
    # assert res.headers['ETag'] != '"{}"'.format(librarie.revision_id)

    # Check that the returned policy matches the given data
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

    # Delete policy/DELETE
    with pytest.raises(IlsRecordError.NotDeleted):
        res = client.delete(item_url)
    assert res.status_code == 200

    res = client.get(item_url)
    assert res.status_code == 200


@mock.patch('rero_ils.modules.circ_policies.views.login_and_librarian',
            mock.MagicMock())
def test_circ_policies_name_validate(client, circ_policy_default_martigny):
    """Test policy validation."""
    url = url_for('circ_policies.name_validate', name='Default')
    circ_policy = circ_policy_default_martigny

    class current_patron:
        class organisation:
            pid = 'org1'
    with mock.patch(
        'rero_ils.modules.circ_policies.views.current_patron',
        current_patron
    ):
        res = client.get(url)
        assert res.status_code == 200
        assert get_json(res) == {'name': 'Default'}

    class current_patron:
        class organisation:
            pid = 'does not exists'
    with mock.patch(
        'rero_ils.modules.circ_policies.views.current_patron',
        current_patron
    ):
        res = client.get(url)
        assert res.status_code == 200
        assert get_json(res) == {'name': None}


def test_circ_policy_secure_api(client, json_header,
                                circ_policy_default_martigny,
                                librarian_martigny,
                                librarian_sion):
    """Test circulation policies secure api access."""
    # Martigny
    login_user_via_session(client, librarian_martigny.user)
    record_url = url_for('invenio_records_rest.cipo_item',
                         pid_value=circ_policy_default_martigny.pid)

    res = client.get(record_url)
    assert res.status_code == 200

    # Sion
    login_user_via_session(client, librarian_sion.user)
    record_url = url_for('invenio_records_rest.cipo_item',
                         pid_value=circ_policy_default_martigny.pid)

    res = client.get(record_url)
    assert res.status_code == 403


def test_circ_policy_secure_api_create(client, json_header,
                                       circ_policy_default_martigny,
                                       system_librarian_martigny,
                                       system_librarian_sion,
                                       circ_policy_default_martigny_data):
    """Test circulation policies secure api create."""
    # Martigny
    login_user_via_session(client, system_librarian_martigny.user)
    post_entrypoint = 'invenio_records_rest.cipo_list'

    del circ_policy_default_martigny_data['pid']
    res, _ = postdata(
        client,
        post_entrypoint,
        circ_policy_default_martigny_data
    )
    assert res.status_code == 201

    # Sion
    login_user_via_session(client, system_librarian_sion.user)

    res, _ = postdata(
        client,
        post_entrypoint,
        circ_policy_default_martigny_data
    )
    assert res.status_code == 403


def test_circ_policy_secure_api_update(client,
                                       circ_policy_short_martigny,
                                       circ_policy_short_martigny_data,
                                       circ_policy_temp_martigny,
                                       circ_policy_temp_martigny_data,
                                       system_librarian_martigny,
                                       system_librarian_sion,
                                       librarian_martigny,
                                       librarian_saxon,
                                       json_header):
    """Test circulation policies secure api update."""
    # Martigny
    login_user_via_session(client, system_librarian_martigny.user)
    record_url = url_for('invenio_records_rest.cipo_item',
                         pid_value=circ_policy_short_martigny.pid)

    data = circ_policy_short_martigny_data
    data['name'] = 'Test Name'
    res = client.put(
        record_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 200

    # Sion
    login_user_via_session(client, system_librarian_sion.user)

    res = client.put(
        record_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 403

    # special case : cipo at library_level
    record_url = url_for('invenio_records_rest.cipo_item',
                         pid_value=circ_policy_temp_martigny.pid)
    login_user_via_session(client, librarian_martigny.user)
    res = client.put(
        record_url,
        data=json.dumps(circ_policy_temp_martigny_data),
        headers=json_header
    )
    assert res.status_code == 200
    login_user_via_session(client, librarian_saxon.user)
    res = client.put(
        record_url,
        data=json.dumps(circ_policy_temp_martigny_data),
        headers=json_header
    )
    assert res.status_code == 403


def test_circ_policy_secure_api_delete(client,
                                       circ_policy_short_martigny,
                                       system_librarian_martigny,
                                       system_librarian_sion,
                                       circ_policy_short_martigny_data,
                                       json_header):
    """Test circulation policies secure api delete."""
    record_url = url_for('invenio_records_rest.cipo_item',
                         pid_value=circ_policy_short_martigny.pid)

    # Martigny
    login_user_via_session(client, system_librarian_martigny.user)
    res = client.delete(record_url)
    assert res.status_code == 204

    # Sion
    login_user_via_session(client, system_librarian_sion.user)
    res = client.delete(record_url)
    assert res.status_code == 410
