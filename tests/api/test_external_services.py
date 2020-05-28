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

    res = client.get(url_for(
        'api_imports.imports_search',
        q='9782070541270:any:ean'
    ))
    assert res.status_code == 200
    assert get_json(res) == {
        'aggregations': {},
        'hits': {
            'hits': [],
            'total': 0
        }
    }
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
    res = client.get(url_for(
        'api_imports.imports_search',
        q='ean:any:123'
    ))
    assert res.status_code == 200
    data = get_json(res)
    assert not data.get('metadata')

    res = client.get(url_for(
        'api_imports.imports_search',
        q='ean:any:9782070541270'
    ))
    assert res.status_code == 200
    data = get_json(res).get('hits').get('hits')[0].get('metadata')
    data.update({
        "$schema": "https://ils.rero.ch/schemas/documents/document-v0.0.1.json"
    })
    assert data == {
        '$schema':
            'https://ils.rero.ch/schemas/documents/document-v0.0.1.json',
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
        'api_imports.imports_search',
        q='ean:any:9782072862014'
    ))
    assert res.status_code == 200
    res_j = get_json(res)
    data = res_j.get('hits').get('hits')[0].get('metadata')
    data.update({
        "$schema": "https://ils.rero.ch/schemas/documents/document-v0.0.1.json"
    })
    assert Document.create(data)
    marc21_link = res_j.get('hits').get('hits')[0].get('links').get('marc21')
    res = client.get(marc21_link)
    data = get_json(res)
    assert data == [
        ['leader', '     cam  22        450 '],
        ['001', 'FRBNF457899220000009'],
        ['003', 'http://catalogue.bnf.fr/ark:/12148/cb457899220'],
        ['010 __', [
            ['a', '978-2-07-286201-4'],
            ['b', 'br.'],
            ['d', '4,90 EUR']
        ]],
        ['020 __', [['a', 'FR'], ['b', '01952290']]],
        ['073 _0', [['a', '9782072862014']]],
        ['100 __', [['a', '20190823d2019    m  y0frey50      ba']]],
        ['101 0_', [['a', 'fre']]],
        ['102 __', [['a', 'FR']]],
        ['105 __', [['a', '||||z   00|y|']]],
        ['106 __', [['a', 'r']]],
        ['181 _0', [['6', '01'], ['a', 'i '], ['b', 'xxxe  ']]],
        ['181 __', [['6', '02'], ['c', 'txt'], ['2', 'rdacontent']]],
        ['182 _0', [['6', '01'], ['a', 'n']]],
        ['182 __', [['6', '02'], ['c', 'n'], ['2', 'rdamedia']]],
        ['200 1_', [
            ['a', 'Les contemplations'],
            ['b', 'Texte imprimé'],
            ['f', 'Victor Hugo'],
            ['g', 'édition établie et annotée par Pierre Albouy...'],
            ['g', '[préface] par Charles Baudelaire']
        ]],
        ['210 __', [
            ['a', '[Paris]'],
            ['c', 'Gallimard'],
            ['d', 'DL 2019'],
            ['e', 'impr. en Espagne']]],
        ['214 _0', [
            ['a', '[Paris]'],
            ['c', 'Gallimard'],
            ['d', 'DL 2019']]],
        ['214 _3', [['a', 'impr. en Espagne']]],
        ['215 __', [['a', '1 vol. (534 p.)'], ['d', '18 cm']]],
        ['225 |_', [['a', 'Folio'], ['i', 'Classique']]],
        ['308 __', [['a', '6678']]],
        ['410 _0', [
            ['0', '34284640'],
            ['t', 'Collection Folio. Classique'],
            ['x', '1258-0449'],
            ['d', '2019']
        ]],
        ['410 _0', [
            ['0', '34234540'],
            ['t', 'Collection Folio'],
            ['x', '0768-0732'],
            ['v', '6678']
        ]],
        ['500 11', [
            ['3', '12044981'],
            ['a', 'Les contemplations'],
            ['m', 'français'],
            ['2', 'lien automatique']]],
        ['686 __', [
            ['a', '801'],
            [
                '2',
                'Cadre de classement de la Bibliographie nationale française'
            ]
        ]],
        ['700 _|', [
            ['3', '11907966'],
            ['o', 'ISNI0000000121200982'],
            ['a', 'Hugo'],
            ['b', 'Victor'],
            ['f', '1802-1885'],
            ['4', '070']
        ]],
        ['702 _|', [
            ['3', '11888332'],
            ['o', 'ISNI0000000117709487'],
            ['a', 'Albouy'],
            ['b', 'Pierre'],
            ['f', '1920-1974'],
            ['4', '340']
        ]],
        ['702 _|', [
            ['3', '11890582'],
            ['o', 'ISNI0000000121221863'],
            ['a', 'Baudelaire'],
            ['b', 'Charles'],
            ['f', '1821-1867'],
            ['4', '080']
        ]],
        ['801 _0', [
            ['a', 'FR'],
            ['b', 'FR-751131015'],
            ['c', '20190823'],
            ['g', 'AFNOR'],
            ['h', 'FRBNF457899220000009'],
            ['2', 'intermrc']]],
        ['930 __', [
            ['5', 'FR-751131010:45789922001001'],
            ['a', '2019-176511'],
            ['b', '759999999'],
            ['c', 'Tolbiac - Rez de Jardin - Littérature et art - Magasin'],
            ['d', 'O']
        ]]
    ]
