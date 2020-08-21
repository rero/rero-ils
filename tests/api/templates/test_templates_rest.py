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

"""Tests REST API for templates."""

import json

import mock
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import VerifyRecordPermissionPatch, get_json, postdata, \
    to_relative_url


def test_templates_permissions(
        client, templ_doc_public_martigny, json_header):
    """Test public template for document retrieval."""
    item_url = url_for('invenio_records_rest.tmpl_item', pid_value='tmpl1')

    res = client.get(item_url)
    assert res.status_code == 401

    res, _ = postdata(
        client,
        'invenio_records_rest.tmpl_list',
        {}
    )
    assert res.status_code == 401

    res = client.put(
        url_for('invenio_records_rest.tmpl_item', pid_value='tmpl1'),
        data={},
        headers=json_header
    )

    res = client.delete(item_url)
    assert res.status_code == 401


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_templates_get(client, templ_doc_public_martigny):
    """Test template retrieval."""
    template = templ_doc_public_martigny
    item_url = url_for('invenio_records_rest.tmpl_item', pid_value='tmpl1')

    res = client.get(item_url)
    assert res.status_code == 200

    assert res.headers['ETag'] == '"{}"'.format(template.revision_id)

    data = get_json(res)
    assert template.dumps() == data['metadata']

    # Check metadata
    for k in ['created', 'updated', 'metadata', 'links']:
        assert k in data

    # Check self links
    res = client.get(to_relative_url(data['links']['self']))
    assert res.status_code == 200
    json = get_json(res)
    assert data == json
    assert template.dumps() == data['metadata']

    list_url = url_for('invenio_records_rest.tmpl_list', pid='tmpl1')
    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)

    assert data['hits']['hits'][0]['metadata'] == template.replace_refs()


def test_filtered_templates_get(
        client, librarian_martigny_no_email, templ_doc_public_martigny,
        templ_doc_private_martigny, librarian_sion_no_email,
        system_librarian_martigny_no_email, librarian_fully_no_email,
        system_librarian_sion_no_email):
    """Test templates filter by organisation."""
    # Martigny
    # system librarian can have access to all templates
    login_user_via_session(client, system_librarian_martigny_no_email.user)
    list_url = url_for('invenio_records_rest.tmpl_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total'] == 2

    # librarian martigny can have access to all public and his templates
    login_user_via_session(client, librarian_martigny_no_email.user)
    list_url = url_for('invenio_records_rest.tmpl_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total'] == 2

    # librarian fully can have access to all public templates only
    login_user_via_session(client, librarian_fully_no_email.user)
    list_url = url_for('invenio_records_rest.tmpl_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total'] == 1

    # Sion
    # librarian sion can have access to no templates
    login_user_via_session(client, librarian_sion_no_email.user)
    list_url = url_for('invenio_records_rest.tmpl_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total'] == 0

    # system librarian sion can have access to no templates
    login_user_via_session(client, system_librarian_sion_no_email.user)
    list_url = url_for('invenio_records_rest.tmpl_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total'] == 0


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_templates_post_put_delete(client, org_martigny,
                                   templ_doc_public_martigny_data,
                                   json_header):
    """Test template post."""
    # Create policy / POST
    item_url = url_for('invenio_records_rest.tmpl_item', pid_value='1')
    list_url = url_for('invenio_records_rest.tmpl_list', q='pid:1')
    del templ_doc_public_martigny_data['pid']
    res, data = postdata(
        client,
        'invenio_records_rest.tmpl_list',
        templ_doc_public_martigny_data
    )
    assert res.status_code == 201

    # Check that the returned template matches the given data
    templ_doc_public_martigny_data['pid'] = '1'

    assert data['metadata'] == templ_doc_public_martigny_data

    res = client.get(item_url)
    assert res.status_code == 200
    data = get_json(res)
    assert templ_doc_public_martigny_data == data['metadata']

    # Update template/PUT
    data = templ_doc_public_martigny_data
    data['name'] = 'Test Name'
    res = client.put(
        item_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 200
    # assert res.headers['ETag'] != '"{}"'.format(librarie.revision_id)

    # Check that the returned template matches the given data
    data = get_json(res)
    assert data['metadata']['name'] == 'Test Name'

    res = client.get(item_url)
    assert res.status_code == 200

    data = get_json(res)
    assert data['metadata']['name'] == 'Test Name'

    res = client.get(list_url)
    assert res.status_code == 200

    data = get_json(res)['hits']['hits'][0]
    assert data['metadata']['name'] == 'Test Name'

    # Delete tempalte/DELETE
    res = client.delete(item_url)
    assert res.status_code == 204

    res = client.get(item_url)
    assert res.status_code == 410


def test_template_secure_api(client, json_header,
                             templ_doc_public_martigny,
                             librarian_martigny_no_email,
                             librarian_sion_no_email):
    """Test templates secure api access."""
    # Martigny
    login_user_via_session(client, librarian_martigny_no_email.user)
    record_url = url_for('invenio_records_rest.tmpl_item',
                         pid_value=templ_doc_public_martigny.pid)

    res = client.get(record_url)
    assert res.status_code == 200

    # Sion
    login_user_via_session(client, librarian_sion_no_email.user)
    record_url = url_for('invenio_records_rest.tmpl_item',
                         pid_value=templ_doc_public_martigny.pid)

    res = client.get(record_url)
    assert res.status_code == 403


def test_template_secure_api_create(client, json_header,
                                    system_librarian_martigny_no_email,
                                    system_librarian_sion_no_email,
                                    templ_doc_public_martigny_data):
    """Test templates secure api create."""
    # Martigny
    login_user_via_session(client, system_librarian_martigny_no_email.user)
    post_entrypoint = 'invenio_records_rest.tmpl_list'

    del templ_doc_public_martigny_data['pid']
    res, _ = postdata(
        client,
        post_entrypoint,
        templ_doc_public_martigny_data
    )
    assert res.status_code == 201

    # Sion
    login_user_via_session(client, system_librarian_sion_no_email.user)

    res, _ = postdata(
        client,
        post_entrypoint,
        templ_doc_public_martigny_data
    )
    assert res.status_code == 403


def test_template_secure_api_update(client,
                                    templ_doc_private_martigny,
                                    templ_doc_private_martigny_data,
                                    system_librarian_martigny_no_email,
                                    system_librarian_sion_no_email,
                                    librarian_martigny_no_email,
                                    librarian_saxon_no_email,
                                    json_header):
    """Test templates secure api update."""
    # Martigny
    login_user_via_session(client, system_librarian_martigny_no_email.user)
    record_url = url_for('invenio_records_rest.tmpl_item',
                         pid_value=templ_doc_private_martigny.pid)

    data = templ_doc_private_martigny_data
    data['name'] = 'Test Name'
    res = client.put(
        record_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 200

    login_user_via_session(client, librarian_martigny_no_email.user)
    data = templ_doc_private_martigny_data
    data['name'] = 'Test Name'
    res = client.put(
        record_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 200

    login_user_via_session(client, librarian_saxon_no_email.user)
    data = templ_doc_private_martigny_data
    data['name'] = 'Test Name'
    res = client.put(
        record_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 403

    # Sion
    login_user_via_session(client, system_librarian_sion_no_email.user)
    res = client.put(
        record_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 403


def test_template_secure_api_delete(client,
                                    templ_doc_private_martigny,
                                    system_librarian_martigny_no_email,
                                    system_librarian_sion_no_email,
                                    templ_doc_public_martigny,
                                    librarian_saxon_no_email,
                                    librarian_martigny_no_email,
                                    json_header):
    """Test templates secure api delete."""
    record_url = url_for('invenio_records_rest.tmpl_item',
                         pid_value=templ_doc_private_martigny.pid)

    # Saxon
    login_user_via_session(client, librarian_saxon_no_email.user)
    res = client.delete(record_url)
    assert res.status_code == 403

    # Sion
    login_user_via_session(client, system_librarian_sion_no_email.user)
    res = client.delete(record_url)
    assert res.status_code == 403

    # Martigny
    login_user_via_session(client, system_librarian_martigny_no_email.user)
    res = client.delete(record_url)
    assert res.status_code == 204

    record_url = url_for('invenio_records_rest.tmpl_item',
                         pid_value=templ_doc_public_martigny.pid)

    # Martigny
    login_user_via_session(client, librarian_martigny_no_email.user)
    res = client.delete(record_url)
    assert res.status_code == 403

    login_user_via_session(client, system_librarian_martigny_no_email.user)
    res = client.delete(record_url)
    assert res.status_code == 204
