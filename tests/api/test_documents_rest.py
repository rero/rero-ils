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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

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
def test_documents_facets(
    client, document, item_lib_martigny, rero_json_header
):
    """Test record retrieval."""
    list_url = url_for('invenio_records_rest.doc_list', view='global')

    res = client.get(list_url, headers=rero_json_header)
    data = get_json(res)
    aggs = data['aggregations']

    # check all facets are present
    for facet in [
        'document_type', 'author__en', 'author__fr',
        'author__de', 'author__it', 'language', 'subject', 'status'
    ]:
        assert aggs[facet]


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_documents_organisation_facets(
    client, document, item_lib_martigny, rero_json_header
):
    """Test record retrieval."""
    list_url = url_for('invenio_records_rest.doc_list', view='global')

    res = client.get(list_url, headers=rero_json_header)
    data = get_json(res)
    aggs = data['aggregations']

    assert 'organisation' in aggs


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_documents_library_facets(
    client, document, org_martigny, item_lib_martigny, rero_json_header
):
    """Test record retrieval."""
    list_url = url_for('invenio_records_rest.doc_list', view='org1')

    res = client.get(list_url, headers=rero_json_header)
    data = get_json(res)
    aggs = data['aggregations']

    assert 'library' in aggs


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_documents_items_filter(
    client, document, org_martigny, item_lib_martigny,
    org_sion, item_lib_sion_org2, rero_json_header
):
    """Test items filters for global and organisation view."""
    list_url = url_for('invenio_records_rest.doc_list', view='global')
    res = client.get(list_url, headers=rero_json_header)
    items = get_json(res)['hits']['hits'][0]['metadata']['items']
    assert len(items) == 2

    list_url = url_for('invenio_records_rest.doc_list', view='org1')
    res = client.get(list_url, headers=rero_json_header)
    items = get_json(res)['hits']['hits'][0]['metadata']['items']
    assert len(items) == 1
    assert items[0]['organisation']['organisation_pid'] == 'org1'

    list_url = url_for('invenio_records_rest.doc_list', view='org2')
    res = client.get(list_url, headers=rero_json_header)
    items = get_json(res)['hits']['hits'][0]['metadata']['items']
    assert len(items) == 1
    assert items[0]['organisation']['organisation_pid'] == 'org2'


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


def test_document_boosting(
        client,
        ebook_1,
        ebook_1_data,
        ebook_4,
        ebook_4_data
):
    """Test document boosting."""
    list_url = url_for(
        'invenio_records_rest.doc_list',
        q='maison'
    )
    res = client.get(list_url)
    hits = get_json(res)['hits']
    assert hits['total'] == 2
    data = hits['hits'][0]['metadata']
    assert data['pid'] == ebook_1_data.get('pid')

    list_url = url_for(
        'invenio_records_rest.doc_list',
        q='title:maison AND authors.name:James'
    )
    res = client.get(list_url)
    hits = get_json(res)['hits']
    assert hits['total'] == 1
    data = hits['hits'][0]['metadata']
    assert data['pid'] == ebook_1_data.get('pid')
