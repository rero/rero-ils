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

"""Tests REST API documents."""

# import json
# from utils import get_json, to_relative_url

import mock
import pytest
from flask import url_for
from utils import VerifyRecordPermissionPatch, get_json, to_relative_url

from rero_ils.modules.documents.api import Document


@pytest.mark.external
@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_documents_get(client, document):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.doc_item', pid_value='doc1')

    res = client.get(item_url)
    assert res.status_code == 200

    assert res.headers['ETag'] == '"{}"'.format(document.revision_id)

    data = get_json(res)
    assert document.dumps() == data['metadata']

    # Check metadata
    for k in ['created', 'updated', 'metadata', 'links']:
        assert k in data

    # Check self links
    res = client.get(to_relative_url(data['links']['self']))
    assert res.status_code == 200
    assert data == get_json(res)
    assert document.dumps() == data['metadata']

    list_url = url_for('invenio_records_rest.doc_list')
    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    document = document.replace_refs()

    assert data['hits']['hits'][0]['metadata'] == \
        document.replace_refs().dumps()

    res = client.get(
        url_for('api_documents.import_bnf_ean', ean='9782070541270'))
    assert res.status_code == 401

    list_url = url_for('invenio_records_rest.doc_list', q="Vincent Berthe")
    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total'] == 1


@pytest.mark.external
@mock.patch('rero_ils.modules.documents.views.login_and_librarian',
            mock.MagicMock())
def test_documents_import_bnf_ean(client):
    """Test document import from bnf."""
    res = client.get(url_for('api_documents.import_bnf_ean', ean='123'))
    assert res.status_code == 404
    data = get_json(res)
    assert not data.get('metadata')

    res = client.get(url_for(
        'api_documents.import_bnf_ean', ean='9782070541270'))
    assert res.status_code == 200
    data = get_json(res).get('metadata')
    data.update({
        "$schema": "https://ils.rero.ch/schema/documents/document-v0.0.1.json"
    })
    assert data == {
        '$schema': 'https://ils.rero.ch/schema/documents/document-v0.0.1.json',
        'authors': [
            {'date': '1965-', 'name': 'Rowling, J. K.', 'type': 'person'},
            {
                'date': '1948-',
                'name': 'Ménard, Jean-François',
                'qualifier': 'romancier pour la jeunesse',
                'type': 'person'
            }
        ],
        'extent': '232 p.',
        'dimensions': ['24 cm'],
        'colorContent': ['rdacc:1003'],
        'identifiedBy': [
            {
                'source': 'BNF',
                'type': 'bf:Local',
                'value': 'ark:/12148/cb37090396w'
            },
            {
                'type': 'bf:Ean',
                'value': '9782070541270'
            }
        ],
        'language': [{'type': 'bf:Language', 'value': 'fre'}],
        'note': [{
            'noteType': 'otherPhysicalDetails',
            'label': 'couv. ill. en coul.'
        }],
        'provisionActivity': [{
            'type': 'bf:Publication',
            'place': [
                {
                    'country': 're',
                    'type': 'bf:Place'
                }
            ],
            'statement': [
                {
                    'label': [
                        {'value': '[Paris]'}
                    ],
                    'type': 'bf:Place'
                },
                {
                    'label': [
                        {'value': 'Gallimard'}
                    ],
                    'type': 'bf:Agent'
                },
                {
                    'label': [
                        {'value': '1999'}
                    ],
                    'type': 'Date'
                },
            ],
            'startDate': 1999,
        }],
        'series': [{'name': 'Harry Potter.', 'number': '1'}],
        'subjects': ['JnRoman'],
        'title': [{
            'mainTitle': [{'value': "Harry Potter à l'école des sorciers"}],
            'type': 'bf:Title'
        }],
        'responsibilityStatement': [
            [{'value': 'J. K. Rowling'}],
            [{'value': "trad. de l'anglais par Jean-François Ménard"}]
        ],
        'titlesProper': ['Harry Potter'],
        'translatedFrom': ['eng'],
        'type': 'book'
    }
    assert Document.create(data)
    res = client.get(url_for(
        'api_documents.import_bnf_ean', ean='9782072862014'))
    assert res.status_code == 200
    data = get_json(res).get('metadata')
    data.update({
        "$schema": "https://ils.rero.ch/schema/documents/document-v0.0.1.json"
    })
    assert Document.create(data)
