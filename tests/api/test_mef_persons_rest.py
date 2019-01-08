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

"""Tests REST API mef_persons."""

# import json
# from utils import get_json, to_relative_url

from flask import url_for
from utils import get_json, to_relative_url


def test_mef_persons_permissions(client, mef_person, json_header):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.pers_item', pid_value='pers1')
    post_url = url_for('invenio_records_rest.pers_list')

    res = client.get(item_url)
    assert res.status_code == 200

    res = client.post(
        post_url,
        data={},
        headers=json_header
    )
    assert res.status_code == 401

    res = client.put(
        url_for('invenio_records_rest.pers_item', pid_value='pers1'),
        data={},
        headers=json_header
    )

    res = client.delete(item_url)
    assert res.status_code == 401


def test_mef_persons_get(client, mef_person):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.pers_item', pid_value='pers1')

    res = client.get(item_url)
    assert res.status_code == 200

    assert res.headers['ETag'] == '"{}"'.format(mef_person.revision_id)

    data = get_json(res)
    assert mef_person.dumps() == data['metadata']

    # Check metadata
    for k in ['created', 'updated', 'metadata', 'links']:
        assert k in data

    # Check self links
    res = client.get(to_relative_url(data['links']['self']))
    assert res.status_code == 200
    assert data == get_json(res)
    assert mef_person.dumps() == data['metadata']

    list_url = url_for('invenio_records_rest.pers_list', pid='pers1')
    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)

    assert data['hits']['hits'][0]['metadata'] == mef_person.replace_refs()
