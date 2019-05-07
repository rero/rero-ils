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

"""Tests REST API locations."""

import json

import mock
from flask import url_for
from utils import VerifyRecordPermissionPatch, get_json, to_relative_url


def test_locations_permissions(client, location, json_header):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.loc_item', pid_value='loc1')
    post_url = url_for('invenio_records_rest.loc_list')

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
def test_locations_get(client, location):
    """Test record retrieval."""
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

    assert data['hits']['hits'][0]['metadata'] == location.replace_refs()


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_locations_post_put_delete(client, library, location_data,
                                   json_header):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.loc_item', pid_value='1')
    post_url = url_for('invenio_records_rest.loc_list')
    list_url = url_for('invenio_records_rest.loc_list', q='pid:1')

    # Create record / POST
    location_data['pid'] = '1'
    res = client.post(
        post_url,
        data=json.dumps(location_data),
        headers=json_header
    )
    assert res.status_code == 201

    # Check that the returned record matches the given data
    data = get_json(res)
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


def test_location_can_delete(client, item_on_shelf, location):
    """Test can delete a location."""
    links = location.get_links_to_me()
    assert 'items' in links

    assert not location.can_delete

    reasons = location.reasons_not_to_delete()
    assert 'links' in reasons
