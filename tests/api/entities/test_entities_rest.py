# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
# Copyright (C) 2019-2023 UCLouvain
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

"""Tests `LocalEntity` resource REST API."""

from flask import url_for
from utils import get_json, postdata


def test_entities_permissions(client, entity_person,
                              local_entity_person, json_header):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.ent_item',
                       pid_value='locent_pers')
    res = client.get(item_url)
    assert res.status_code == 401

    item_url = url_for('invenio_records_rest.ent_item',
                       pid_value='ent_pers')
    res = client.get(item_url)
    assert res.status_code == 401

    res = client.get(url_for('invenio_records_rest.ent_list'))
    assert res.status_code == 200

    res, _ = postdata(client, 'invenio_records_rest.ent_list', {})
    assert res.status_code == 401

    client.put(
        url_for('invenio_records_rest.ent_item', pid_value='ent_pers'),
        data={},
        headers=json_header
    )

    res = client.delete(item_url)
    assert res.status_code == 401


def test_entities_get(client, entity_person, local_entity_person):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.ent_item',
                       pid_value='locent_pers')
    res = client.get(item_url)
    assert res.status_code == 401

    item_url = url_for('invenio_records_rest.ent_item',
                       pid_value='ent_pers')
    res = client.get(item_url)
    assert res.status_code == 401

    res = client.get(url_for('invenio_records_rest.ent_list'))
    assert res.status_code == 200

    # Check remote/local entities self links
    data = get_json(res)
    pid_link_map = {
        'ent_pers': 'http://localhost/remote_entities/ent_pers',
        'locent_pers': 'http://localhost/local_entities/locent_pers'
    }
    for hit in data['hits']['hits']:
        assert hit['links']['self'] == pid_link_map.get(hit['id'])

    # search entity record
    list_url = url_for('invenio_records_rest.ent_list', pid='ent_pers')
    res = client.get(list_url)
    assert res.status_code == 200

    # search local entity record
    list_url = url_for('invenio_records_rest.ent_list', pid='locent_pers')
    res = client.get(list_url)
    assert res.status_code == 200
