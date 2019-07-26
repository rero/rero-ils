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

"""Tests REST API documents."""

# import json
# from utils import get_json, to_relative_url

import mock
import pytest
from flask import url_for
from utils import VerifyRecordPermissionPatch, get_json, to_relative_url


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
    assert data['hits']['hits'][0]['metadata'] == document.replace_refs()

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
    data = get_json(res)
    assert data.get('metadata') == {
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
        'formats': ['24 cm'],
        'identifiers': {
            'bnfID': 'cb37090396w',
            'isbn': '9782070541270'
        },
        'languages': [
            {'language': 'fre'}
        ],
        'otherMaterialCharacteristics': 'couv. ill. en coul.',
        'publicationYear': 1999,
        'publishers': [
            {'name': ['Gallimard'], 'place': ['[Paris]']}
        ],
        'series': [{'name': 'Harry Potter.', 'number': '1'}],
        'subjects': ['JnRoman'],
        'title': "Harry Potter à l'école des sorciers",
        'titlesProper': ['Harry Potter'],
        'translatedFrom': ['eng'],
        'type': 'book'
    }
