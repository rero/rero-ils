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

import json

import mock
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import VerifyRecordPermissionPatch, get_json, postdata

from rero_ils.modules.documents.utils import clean_text
from rero_ils.modules.documents.views import can_request, \
    item_library_pickup_locations, item_status_text, number_of_requests, \
    patron_request_rank, requested_this_item


def test_documents_permissions(client, document, json_header):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.doc_item', pid_value='doc1')

    res = client.get(item_url)
    assert res.status_code == 200

    res, _ = postdata(
        client,
        'invenio_records_rest.doc_list',
        {}
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
def test_documents_post_put_delete(
        client,
        document_chinese_data,
        json_header,
        rero_json_header):
    """Test record retrieval."""
    # Create record / POST
    item_url = url_for('invenio_records_rest.doc_item', pid_value='4')
    list_url = url_for('invenio_records_rest.doc_list', q='pid:4')

    document_chinese_data['pid'] = '4'
    res, data = postdata(
        client,
        'invenio_records_rest.doc_list',
        document_chinese_data
    )

    assert res.status_code == 201

    # Check that the returned record matches the given data
    assert clean_text(data['metadata']) == document_chinese_data

    res = client.get(item_url)
    assert res.status_code == 200
    data = get_json(res)

    assert clean_text(data['metadata']) == document_chinese_data
    expected_title = [
        {
            '_text': '\u56fd\u9645\u6cd5 : subtitle (Chinese). '
                     'Part Number (Chinese), Part Name (Chinese) = '
                     'International law (Chinese) : '
                     'Parallel Subtitle (Chinese). '
                     'Parallel Part Number (Chinese), '
                     'Parallel Part Name (Chinese) = '
                     'Parallel Title 2 (Chinese) : '
                     'Parallel Subtitle 2 (Chinese)',
            'mainTitle': [
                    {'value': 'Guo ji fa'},
                    {
                        'value': '\u56fd\u9645\u6cd5',
                        'language': 'chi-hani'
                    }
            ],
            'subtitle': [
                {'value': 'subtitle (Latin)'},
                {
                    'value': 'subtitle (Chinese)',
                    'language': 'chi-hani'
                }
            ],
            'part': [{
                'partNumber': [
                    {'value': 'Part Number (Latin)'},
                    {
                        'value': 'Part Number (Chinese)',
                        'language': 'chi-hani'
                    }
                ],
                'partName': [
                    {'value': 'Part Name (Latin)'},
                    {
                        'language': 'chi-hani',
                        'value': 'Part Name (Chinese)'
                    }
                ]
            }],
            'type': 'bf:Title'
        },
        {
            'mainTitle': [
                {'value': 'International law (Latin)'},
                {
                    'value': 'International law (Chinese)',
                    'language': 'chi-hani'
                }
            ],
            'subtitle': [
                {'value': 'Parallel Subtitle (Latin)'},
                {
                    'value': 'Parallel Subtitle (Chinese)',
                    'language': 'chi-hani'
                }
            ],
            'part': [{
                'partNumber': [
                    {'value': 'Parallel Part Number (Latin)'},
                    {
                        'value': 'Parallel Part Number (Chinese)',
                        'language': 'chi-hani'
                    }
                ],
                'partName': [
                    {'value': 'Parallel Part Name (Latin)'},
                    {
                        'language': 'chi-hani',
                        'value': 'Parallel Part Name (Chinese)'
                    }
                ]
            }],

            'type': 'bf:ParallelTitle'
        },
        {
            'mainTitle': [
                {'value': 'Parallel Title 2 (Latin)'},
                {
                    'value': 'Parallel Title 2 (Chinese)',
                    'language': 'chi-hani'
                }
            ],
            'subtitle': [
                {'value': 'Parallel Subtitle 2 (Latin)'},
                {
                    'value': 'Parallel Subtitle 2 (Chinese)',
                    'language': 'chi-hani'
                }
            ],
            'type': 'bf:ParallelTitle'
        },
        {
            'mainTitle': [{'value': 'Guojifa'}],
            'type': 'bf:VariantTitle'
        }
    ]

    # Update record/PUT
    data = document_chinese_data
    res = client.put(
        item_url,
        data=json.dumps(data),
        headers=rero_json_header
    )
    assert res.status_code == 200
    # assert res.headers['ETag'] != '"{}"'.format(librarie.revision_id)

    # Check that the returned record matches the given data
    data = get_json(res)
    assert data['metadata']['title'] == expected_title
    assert data['metadata']['ui_title_variants'] == ['Guojifa']
    assert data['metadata']['ui_title_altgr'] == \
        ['Guo ji fa : subtitle (Latin). Part Number (Latin), Part Name (Latin)'
         ' = International law (Latin) : Parallel Subtitle (Latin).'
         ' Parallel Part Number (Latin), Parallel Part Name (Latin)'
         ' = Parallel Title 2 (Latin) : Parallel Subtitle 2 (Latin)']
    assert data['metadata']['ui_responsibilities'] == [
        '梁西原著主编, 王献枢副主编',
        'Liang Xi yuan zhu zhu bian, Wang Xianshu fu zhu bian'
    ]

    res = client.get(item_url)
    assert res.status_code == 200

    data = get_json(res)
    assert data['metadata']['title'] == expected_title

    res = client.get(list_url)
    assert res.status_code == 200

    data = get_json(res)['hits']['hits'][0]
    assert data['metadata']['title'] == expected_title

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
        q='autocomplete_title:maison AND authors.name:James'
    )
    res = client.get(list_url)
    hits = get_json(res)['hits']
    assert hits['total'] == 1
    data = hits['hits'][0]['metadata']
    assert data['pid'] == ebook_1_data.get('pid')
