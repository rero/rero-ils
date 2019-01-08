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

"""Tests REST API patron_types."""

# import json
# from utils import get_json, to_relative_url

import json

import mock
from flask import url_for
from utils import VerifyRecordPermissionPatch, get_json, to_relative_url


def test_patron_types_permissions(client, patron_type, json_header):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.ptty_item', pid_value='ptty1')
    post_url = url_for('invenio_records_rest.ptty_list')

    res = client.get(item_url)
    assert res.status_code == 401

    res = client.post(
        post_url,
        data={},
        headers=json_header
    )
    assert res.status_code == 401

    res = client.put(
        url_for('invenio_records_rest.ptty_item', pid_value='ptty1'),
        data={},
        headers=json_header
    )

    res = client.delete(item_url)
    assert res.status_code == 401

    res = client.get(url_for('patron_types.name_validate', name='standard'))
    assert res.status_code == 401


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_patron_types_get(client, patron_type):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.ptty_item', pid_value='ptty1')

    res = client.get(item_url)
    assert res.status_code == 200

    assert res.headers['ETag'] == '"{}"'.format(patron_type.revision_id)

    data = get_json(res)
    assert patron_type.dumps() == data['metadata']

    # Check metadata
    for k in ['created', 'updated', 'metadata', 'links']:
        assert k in data

    # Check self links
    res = client.get(to_relative_url(data['links']['self']))
    assert res.status_code == 200
    assert data == get_json(res)
    assert patron_type.dumps() == data['metadata']

    list_url = url_for('invenio_records_rest.ptty_list', pid='ptty1')
    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)

    assert data['hits']['hits'][0]['metadata'] == patron_type.replace_refs()


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_patron_types_post_put_delete(client, organisation, patron_type_data,
                                      json_header):
    """Test record retrieval."""
    # Create record / POST
    item_url = url_for('invenio_records_rest.ptty_item', pid_value='1')
    post_url = url_for('invenio_records_rest.ptty_list')
    list_url = url_for('invenio_records_rest.ptty_list', q='pid:1')

    patron_type_data['pid'] = '1'
    res = client.post(
        post_url,
        data=json.dumps(patron_type_data),
        headers=json_header
    )
    assert res.status_code == 201

    # Check that the returned record matches the given data
    data = get_json(res)
    assert data['metadata'] == patron_type_data

    res = client.get(item_url)
    assert res.status_code == 200
    data = get_json(res)
    assert patron_type_data == data['metadata']

    # Update record/PUT
    data = patron_type_data
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


@mock.patch('rero_ils.modules.patron_types.views.login_and_librarian',
            mock.MagicMock())
def test_patron_types_name_validate(client, patron_type):

    url = url_for('patron_types.name_validate', name='standard')

    class current_patron:
        class organisation:
            pid = 'org1'
    with mock.patch(
        'rero_ils.modules.patron_types.views.current_patron',
        current_patron
    ):
        res = client.get(url)
        assert res.status_code == 200
        assert get_json(res) == {'name': 'standard'}

    class current_patron:
        class organisation:
            pid = 'does not exists'
    with mock.patch(
        'rero_ils.modules.patron_types.views.current_patron',
        current_patron
    ):
        res = client.get(url)
        assert res.status_code == 200
        assert get_json(res) == {'name': None}
