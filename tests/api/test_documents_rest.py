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

import json

import mock
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import VerifyRecordPermissionPatch, get_json, to_relative_url

from rero_ils.modules.documents.views import can_request, \
    item_library_pickup_locations, item_status_text, number_of_requests, \
    patron_request_rank, requested_this_item


def test_documents_permissions(client, document, json_header):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.doc_item', pid_value='doc1')
    post_url = url_for('invenio_records_rest.doc_list')

    res = client.get(item_url)
    assert res.status_code == 200

    res = client.post(
        post_url,
        data={},
        headers=json_header
    )
    assert res.status_code == 401

    res = client.put(
        url_for('invenio_records_rest.doc_item', pid_value='doc1'),
        data={},
        headers=json_header
    )

    res = client.delete(item_url)
    assert res.status_code == 401


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


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_documents_facets(client, document, item_lib_martigny,
                          rero_json_header, lib_martigny):
    """Test record retrieval."""
    list_url = url_for('invenio_records_rest.doc_list')

    res = client.get(list_url, headers=rero_json_header)
    data = get_json(res)
    aggs = data['aggregations']

    # check all facets are present
    for facet in [
        'document_type', 'library', 'author__en', 'author__fr', 'author__de',
        'author__it', 'language', 'subject', 'status'
    ]:
        assert aggs[facet]
    # check library name for display
    assert aggs['library']['buckets'][0]['name'] == lib_martigny['name']


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_documents_post_put_delete(client, document_data,
                                   json_header):
    """Test record retrieval."""
    # Create record / POST
    item_url = url_for('invenio_records_rest.doc_item', pid_value='1')
    post_url = url_for('invenio_records_rest.doc_list')
    list_url = url_for('invenio_records_rest.doc_list', q='pid:1')

    document_data['pid'] = '1'
    res = client.post(
        post_url,
        data=json.dumps(document_data),
        headers=json_header
    )
    assert res.status_code == 201

    # Check that the returned record matches the given data
    data = get_json(res)
    assert data['metadata'] == document_data

    res = client.get(item_url)
    assert res.status_code == 200
    data = get_json(res)
    assert document_data == data['metadata']

    # Update record/PUT
    data = document_data
    data['title'] = 'Test Name'
    res = client.put(
        item_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 200
    # assert res.headers['ETag'] != '"{}"'.format(librarie.revision_id)

    # Check that the returned record matches the given data
    data = get_json(res)
    assert data['metadata']['title'] == 'Test Name'

    res = client.get(item_url)
    assert res.status_code == 200

    data = get_json(res)
    assert data['metadata']['title'] == 'Test Name'

    res = client.get(list_url)
    assert res.status_code == 200

    data = get_json(res)['hits']['hits'][0]
    assert data['metadata']['title'] == 'Test Name'

    # Delete record/DELETE
    res = client.delete(item_url)
    assert res.status_code == 204

    res = client.get(item_url)
    assert res.status_code == 410


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


def test_document_can_delete(client, item_lib_martigny, loan_pending_martigny,
                             document):
    """Test can delete a document."""
    links = document.get_links_to_me()
    assert 'items' in links
    assert 'loans' in links

    assert not document.can_delete

    reasons = document.reasons_not_to_delete()
    assert 'links' in reasons


def test_document_can_request_view(client, item_lib_fully,
                                   loan_pending_martigny, document,
                                   patron_martigny_no_email,
                                   patron2_martigny_no_email,
                                   item_type_standard_martigny,
                                   circulation_policies,
                                   librarian_martigny_no_email,
                                   item_lib_martigny,
                                   item_lib_saxon,
                                   item_lib_sion,
                                   loc_public_martigny):
    """Test can request on document view."""
    login_user_via_session(client, patron_martigny_no_email.user)

    assert not patron_request_rank(item_lib_fully)

    with mock.patch(
        'rero_ils.modules.documents.views.current_user',
        patron_martigny_no_email.user
    ):
        assert can_request(item_lib_fully)
        assert not requested_this_item(item_lib_fully)
        assert number_of_requests(item_lib_fully) == 1
        assert number_of_requests(item_lib_martigny) == 0
        assert not can_request(item_lib_sion)

    with mock.patch(
        'rero_ils.modules.documents.views.current_user',
        patron2_martigny_no_email.user
    ):
        assert not can_request(item_lib_fully)
        assert requested_this_item(item_lib_fully)
        assert patron_request_rank(item_lib_fully)

    status = item_status_text(item_lib_fully, format='medium', locale='en')
    assert status == 'not available (requested)'

    status = item_status_text(item_lib_martigny, format='medium', locale='en')
    assert status == 'available'

    picks = item_library_pickup_locations(item_lib_fully)
    assert len(picks) == 3

    picks = item_library_pickup_locations(item_lib_martigny)
    assert len(picks) == 3
