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

"""Tests `Entity` resource REST API."""

import mock
from flask import url_for
from utils import get_json, mock_response, postdata, to_relative_url

from rero_ils.modules.entities.dumpers import indexer_dumper
from rero_ils.modules.entities.models import EntityType


def test_remote_entities_permissions(client, entity_person, json_header):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.rement_item',
                       pid_value='ent_pers')
    res = client.get(item_url)
    assert res.status_code == 200

    res, _ = postdata(client, 'invenio_records_rest.rement_list', {})
    assert res.status_code == 401

    client.put(
        url_for('invenio_records_rest.rement_item', pid_value='ent_pers'),
        data={},
        headers=json_header
    )

    res = client.delete(item_url)
    assert res.status_code == 401


def test_remote_entities_get(client, entity_person):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.rement_item',
                       pid_value='ent_pers')

    res = client.get(item_url)
    assert res.status_code == 200
    assert res.headers['ETag'] == f'"{entity_person.revision_id}"'

    data = get_json(res)
    assert entity_person.dumps() == data['metadata']

    # Check metadata
    for k in ['created', 'updated', 'metadata', 'links']:
        assert k in data

    # Check self links
    res = client.get(to_relative_url(data['links']['self']))
    assert res.status_code == 200
    assert data == get_json(res)
    assert entity_person.dumps() == data['metadata']

    list_url = url_for('invenio_records_rest.rement_list', pid='ent_pers')
    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    entity_person = entity_person.replace_refs()
    entity_person['organisations'] = entity_person.organisation_pids
    entity_person['type'] = EntityType.PERSON
    assert data['hits']['hits'][0]['metadata'] == \
           entity_person.dumps(indexer_dumper)


@mock.patch('rero_ils.modules.decorators.login_and_librarian',
            mock.MagicMock())
@mock.patch('requests.request')
def test_remote_search_proxy(
    mock_es_concept_get, app, client,
    mef_concept2_es_response, mef_agents1_es_response, mef_places1_es_response
):
    """Test entities search on remote servers."""
    # TEST#1 :: Concepts
    #    All results must include a `type` key if a root `metadata` field
    #    exists.
    mock_es_concept_get.return_value = mock_response(
        json_data=mef_concept2_es_response)

    response = client.get(url_for(
        'api_remote_entities.remote_search_proxy',
        entity_type='concepts-genreForm',
        term='side-car'
    ))
    assert response.status_code == 200

    assert all(
        hit.get('metadata', {}).get('type') == EntityType.TOPIC
        for hit in response.json['hits']['hits']
        if 'metadata' in hit
    )

    # TEST#2 :: Agents
    #   All result must include a `identifiedBy` object if a root
    mock_es_concept_get.return_value = mock_response(
        json_data=mef_agents1_es_response)
    response = client.get(url_for(
        'api_remote_entities.remote_search_proxy',
        entity_type='agents',
        term='UCLouvain'
    ))
    identifier = mef_agents1_es_response['hits']['hits'][0][
        'metadata']['idref']['identifier']
    assert identifier == response.json['hits']['hits'][0][
        'metadata']['idref']['identifiedBy'][0]['value']

    # TEST#3 :: Places
    #   All result must include a `identifiedBy` object if a root
    mock_es_concept_get.return_value = mock_response(
        json_data=mef_places1_es_response)
    response = client.get(url_for(
        'api_remote_entities.remote_search_proxy',
        entity_type='places',
        term='Rouen'
    ))
    authorized_access_point = mef_places1_es_response['hits']['hits'][0][
        'metadata']['idref']['authorized_access_point']
    assert authorized_access_point == response.json['hits']['hits'][0][
        'metadata']['idref']['authorized_access_point']

    # TEST#4 :: Unknown MEF search type
    #   Try to execute a search on a not-configured MEF category. It should be
    #   raised a `ValueError` caught by flask to return an HTTP 400 response
    category = 'unknown_category'
    response = client.get(url_for(
        'api_remote_entities.remote_search_proxy',
        entity_type=category,
        term='search_term'
    ))
    assert response.status_code == 400
    assert response.json['message'] == \
           f'Unable to find a MEF factory for {category}'

    # TEST#4 :: Simulate MEF errors
    #   Simulate than MEF call return an HTTP error and check the response.
    mock_es_concept_get.return_value = mock_response(status=404)
    response = client.get(url_for(
        'api_remote_entities.remote_search_proxy',
        entity_type='agents',
        term='UCLouvain'
    ))
    assert response.status_code == 404
