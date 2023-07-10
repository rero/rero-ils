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

import json

import mock
from flask import url_for
from utils import VerifyRecordPermissionPatch, get_json, postdata, \
    to_relative_url

from rero_ils.modules.documents.dumpers import document_replace_refs_dumper
from rero_ils.modules.entities.dumpers import indexer_dumper
from rero_ils.modules.entities.local_entities.api import LocalEntity
from rero_ils.modules.entities.models import EntityType
from rero_ils.modules.utils import get_ref_for_pid


def test_local_entities_permissions(client, roles, local_entity_person,
                                    json_header):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.locent_item',
                       pid_value='locent_pers')
    res = client.get(item_url)
    assert res.status_code == 200

    res, _ = postdata(client, 'invenio_records_rest.locent_list', {})
    assert res.status_code == 401

    client.put(
        url_for('invenio_records_rest.locent_item', pid_value='locent_pers'),
        data={},
        headers=json_header
    )
    assert res.status_code == 401

    res = client.delete(item_url)
    assert res.status_code == 401


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_local_entities_get(client, local_entity_person):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.locent_item',
                       pid_value='locent_pers')

    res = client.get(item_url)
    assert res.status_code == 200
    assert res.headers['ETag'] == f'"{local_entity_person.revision_id}"'

    data = get_json(res)
    assert local_entity_person.dumps() == data['metadata']

    # Check metadata
    for k in ['created', 'updated', 'metadata', 'links']:
        assert k in data

    # Check self links
    res = client.get(to_relative_url(data['links']['self']))
    assert res.status_code == 200
    assert data == get_json(res)

    assert local_entity_person.dumps() == data['metadata']

    list_url = url_for('invenio_records_rest.locent_list', pid='locent_pers')
    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    entity_person = local_entity_person.replace_refs()
    entity_person['type'] = EntityType.PERSON
    assert data['hits']['hits'][0]['metadata'] == \
           entity_person.dumps(dumper=indexer_dumper)


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_local_entities_post_put_delete(client, local_entity_person_data,
                                        json_header):
    """Test record api post, put and delete."""
    item_url = url_for('invenio_records_rest.locent_item', pid_value='1')
    list_url = url_for('invenio_records_rest.locent_list', q='pid:1')
    local_entity_data = local_entity_person_data
    # Create record / POST
    local_entity_data['pid'] = '1'
    res, data = postdata(
        client,
        'invenio_records_rest.locent_list',
        local_entity_data
    )
    assert res.status_code == 201
    local_entity = LocalEntity.get_record_by_pid(data['metadata']['pid'])
    # Check that the returned record matches the given data
    assert local_entity.dumps() == data['metadata']

    res = client.get(item_url)
    assert res.status_code == 200
    data = get_json(res)

    assert local_entity.dumps() == data['metadata']

    # Update record/PUT
    data = local_entity_data
    data['name'] = 'Test Name'
    res = client.put(
        item_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 200

    # Check that the returned record matches the given data
    data = get_json(res)
    assert data['metadata']['name'] == 'Test Name'

    # Check value from record API
    res = client.get(item_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['metadata']['name'] == 'Test Name'

    # Check value from Elasticsearch
    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)['hits']['hits'][0]
    assert data['metadata']['name'] == 'Test Name'

    # Delete record/DELETE
    res = client.delete(item_url)
    assert res.status_code == 204

    res = client.get(item_url)
    assert res.status_code == 410


@mock.patch('rero_ils.modules.decorators.login_and_librarian',
            mock.MagicMock())
def test_local_search_by_proxy(
    client, local_entity_genre_form, local_entity_org
):
    """Test local entity search proxy."""
    response = client.get(url_for(
        'api_local_entities.local_search_proxy',
        entity_type='concepts-genreForm',
        term='personal',
        size='dummy_qs_arg'
    ))
    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]['pid'] == local_entity_genre_form.pid

    response = client.get(url_for(
        'api_local_entities.local_search_proxy',
        entity_type='concepts-genreForm',
        term='personal',
        size='0'
    ))
    assert response.status_code == 200
    assert len(response.json) == 0

    response = client.get(url_for(
        'api_local_entities.local_search_proxy',
        entity_type='concepts-genreForm',
        term='dummy_key'
    ))
    assert response.status_code == 200
    assert len(response.json) == 0

    response = client.get(url_for(
        'api_local_entities.local_search_proxy',
        entity_type='bf:Organisation',
        term='Convegno'
    ))
    assert response.status_code == 200
    assert len(response.json) == 1
    assert response.json[0]['pid'] == local_entity_org.pid


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_local_entities_resolve(
    client, mef_agents_url, local_entity_person, document
):
    """Test local entity resolver"""

    # LOCAL ENTITY RESOLVER ===================================================
    res = client.get(url_for(
        'invenio_records_rest.locent_item',
        pid_value=local_entity_person.pid,
        resolve='1'
    ))
    assert res.status_code == 200

    # LOCAL ENTITY INTO A DOCUMENT RESOLVER ===================================
    ent_ref = get_ref_for_pid('locent', local_entity_person.pid)
    document.setdefault('contribution', []).append({
        'entity': {'$ref': ent_ref},
        'role': ['aut']
    })
    document = document.update(document, dbcommit=True, reindex=True)
    data = document.dumps(dumper=document_replace_refs_dumper)
    assert any(
        contribution['entity'].get('pid') == local_entity_person.pid
        for contribution in data['contribution']
    )
