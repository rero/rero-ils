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
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import VerifyRecordPermissionPatch, get_json, postdata, \
    to_relative_url


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_circ_policies_get(client, circ_policy_default_martigny):
    """Test policy retrieval."""
    circ_policy = circ_policy_default_martigny
    item_url = url_for('invenio_records_rest.cipo_item', pid_value='cipo1')

    res = client.get(item_url)
    assert res.status_code == 200

    assert res.headers['ETag'] == f'"{circ_policy.revision_id}"'

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
                                       circ_policy_short_martigny_data,
                                       json_header):
    """Test policy retrieval."""
    # Create policy / POST
    item_url = url_for('invenio_records_rest.cipo_item', pid_value='1')
    list_url = url_for('invenio_records_rest.cipo_list', q='pid:1')
    del circ_policy_short_martigny_data['pid']
    res, data = postdata(
        client,
        'invenio_records_rest.cipo_list',
        circ_policy_short_martigny_data
    )
    assert res.status_code == 201

    # Check that the returned policy matches the given data
    circ_policy_short_martigny_data['pid'] = '1'
    assert data['metadata'] == circ_policy_short_martigny_data
    res = client.get(item_url)
    assert res.status_code == 200
    data = get_json(res)
    assert circ_policy_short_martigny_data == data['metadata']

    # Update policy/PUT
    data = circ_policy_short_martigny_data
    data['name'] = 'Test Name'
    res = client.put(
        item_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 200
    # assert res.headers['ETag'] != f'"{librarie.revision_id}"'

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
    res = client.delete(item_url)
    assert res.status_code == 204


@mock.patch('rero_ils.modules.decorators.login_and_librarian',
            mock.MagicMock())
def test_circ_policies_name_validate(client):
    """Test policy validation."""
    url = url_for('circ_policies.name_validate', name='Default')

    class current_librarian:
        class organisation:
            pid = 'org1'
    with mock.patch(
        'rero_ils.modules.circ_policies.views.current_librarian',
        current_librarian
    ):
        res = client.get(url)
        assert res.status_code == 200
        assert get_json(res) == {'name': 'Default'}

    class current_librarian:
        class organisation:
            pid = 'does not exists'
    with mock.patch(
        'rero_ils.modules.circ_policies.views.current_librarian',
        current_librarian
    ):
        res = client.get(url)
        assert res.status_code == 200
        assert get_json(res) == {'name': None}
