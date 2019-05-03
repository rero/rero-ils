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

"""Tests REST API for circulation policies."""

import json

import mock
import pytest
from flask import url_for
from utils import VerifyRecordPermissionPatch, get_json, to_relative_url

from rero_ils.modules.api import IlsRecordError


def test_circ_policies_permissions(
        client, circ_policy, json_header):
    """Test policy retrieval."""
    item_url = url_for('invenio_records_rest.cipo_item', pid_value='cipo1')
    post_url = url_for('invenio_records_rest.cipo_list')

    res = client.get(item_url)
    assert res.status_code == 401

    res = client.post(
        post_url,
        data={},
        headers=json_header
    )
    assert res.status_code == 401

    res = client.put(
        url_for('invenio_records_rest.cipo_item', pid_value='cipo1'),
        data={},
        headers=json_header
    )

    res = client.delete(item_url)
    assert res.status_code == 403

    res = client.get(url_for('circ_policies.name_validate', name='standard'))
    assert res.status_code == 401


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_circ_policies_get(client, circ_policy):
    """Test policy retrieval."""
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


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_circ_policies_post_put_delete(client, organisation, circ_policy_data,
                                       json_header, can_delete_json_header):
    """Test policy retrieval."""
    # Create policy / POST
    item_url = url_for('invenio_records_rest.cipo_item', pid_value='1')
    post_url = url_for('invenio_records_rest.cipo_list')
    list_url = url_for('invenio_records_rest.cipo_list', q='pid:1')
    del circ_policy_data['pid']
    res = client.post(
        post_url,
        data=json.dumps(circ_policy_data),
        headers=json_header
    )
    assert res.status_code == 201

    # Check that the returned policy matches the given data
    data = get_json(res)
    circ_policy_data['pid'] = '1'

    assert data['metadata'] == circ_policy_data

    res = client.get(item_url)
    assert res.status_code == 200
    data = get_json(res)
    assert circ_policy_data == data['metadata']

    # Update policy/PUT
    data = circ_policy_data
    data['name'] = 'Test Name'
    res = client.put(
        item_url,
        data=json.dumps(data),
        headers=can_delete_json_header
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
def test_circ_policies_name_validate(client, circ_policy):
    """Test policy validation."""
    url = url_for('circ_policies.name_validate', name='standard')

    class current_patron:
        class organisation:
            pid = 'org1'
    with mock.patch(
        'rero_ils.modules.circ_policies.views.current_patron',
        current_patron
    ):
        res = client.get(url)
        assert res.status_code == 200
        assert get_json(res) == {'name': 'standard'}

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
