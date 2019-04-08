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

# import json
# from utils import get_json, to_relative_url

import json

import mock
from flask import url_for
from utils import VerifyRecordPermissionPatch, get_json, to_relative_url


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
def test_libraries_post_put_delete(client, org_martigny, lib_martigny_data,
                                   json_header):
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
