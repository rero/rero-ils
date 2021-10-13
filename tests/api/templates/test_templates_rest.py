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

from rero_ils.modules.utils import get_ref_for_pid


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

    list_url = url_for('invenio_records_rest.tmpl_list', q='pid:tmpl1')
    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)

    tmpl_data = template.replace_refs()
    tmpl_data.pop('data', None)
    assert data['hits']['hits'][0]['metadata'] == tmpl_data


def test_filtered_templates_get(
        client, librarian_martigny, templ_doc_public_martigny,
        templ_doc_private_martigny, librarian_sion,
        system_librarian_martigny, librarian_fully,
        system_librarian_sion):
    """Test templates filter by organisation."""
    # Martigny
    # system librarian can have access to all templates
    login_user_via_session(client, system_librarian_martigny.user)
    list_url = url_for('invenio_records_rest.tmpl_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total']['value'] == 2

    # librarian martigny can have access to all public and his templates
    login_user_via_session(client, librarian_martigny.user)
    list_url = url_for('invenio_records_rest.tmpl_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total']['value'] == 2

    # librarian fully can have access to all public templates only
    login_user_via_session(client, librarian_fully.user)
    list_url = url_for('invenio_records_rest.tmpl_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total']['value'] == 1

    # Sion
    # librarian sion can have access to no templates
    login_user_via_session(client, librarian_sion.user)
    list_url = url_for('invenio_records_rest.tmpl_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total']['value'] == 0

    # system librarian sion can have access to no templates
    login_user_via_session(client, system_librarian_sion.user)
    list_url = url_for('invenio_records_rest.tmpl_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total']['value'] == 0


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_templates_post_put_delete(client, org_martigny,
                                   system_librarian_martigny,
                                   templ_doc_public_martigny_data,
                                   json_header):
    """Test template post."""
    # Create policy / POST
    item_url = url_for('invenio_records_rest.tmpl_item', pid_value='foo1')
    list_url = url_for('invenio_records_rest.tmpl_list', q='pid:foo1')
    templ_doc_public_martigny_data['pid'] = 'foo1'
    res, data = postdata(
        client,
        'invenio_records_rest.tmpl_list',
        templ_doc_public_martigny_data
    )
    assert res.status_code == 201

    # Check that the returned template matches the given data
    templ_doc_public_martigny_data['pid'] = 'foo1'
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
                             librarian_martigny,
                             librarian_sion):
    """Test templates secure api access."""
    # Martigny
    login_user_via_session(client, librarian_martigny.user)
    record_url = url_for('invenio_records_rest.tmpl_item',
                         pid_value=templ_doc_public_martigny.pid)

    res = client.get(record_url)
    assert res.status_code == 200

    # Sion
    login_user_via_session(client, librarian_sion.user)
    record_url = url_for('invenio_records_rest.tmpl_item',
                         pid_value=templ_doc_public_martigny.pid)

    res = client.get(record_url)
    assert res.status_code == 403


def test_template_secure_api_create(client, json_header,
                                    system_librarian_martigny,
                                    system_librarian_sion,
                                    templ_doc_public_martigny_data,
                                    templ_item_public_martigny,
                                    templ_hold_public_martigny,
                                    templ_patron_public_martigny):
    """Test templates secure api create."""
    # Martigny
    login_user_via_session(client, system_librarian_martigny.user)
    post_entrypoint = 'invenio_records_rest.tmpl_list'

    # test template creation for documents
    del templ_doc_public_martigny_data['pid']
    # add a pid to the record data
    templ_doc_public_martigny_data['data']['pid'] = 'toto'
    res, _ = postdata(
        client,
        post_entrypoint,
        templ_doc_public_martigny_data
    )
    assert res.status_code == 201
    # ensure that pid is removed from recordds
    assert 'pid' not in res.json['metadata']['data']

    # test template creation for items
    del templ_item_public_martigny['pid']
    # add fields that will be removed at the creation of the template.
    templ_item_public_martigny['data']['pid'] = 'toto'
    templ_item_public_martigny['data']['barcode'] = 'toto'
    templ_item_public_martigny['data']['status'] = 'on_loan'
    templ_item_public_martigny['data']['library'] = \
        {'$ref': get_ref_for_pid('lib', 'toto')}
    templ_item_public_martigny['data']['document'] = \
        {'$ref': get_ref_for_pid('doc', 'toto')}
    templ_item_public_martigny['data']['holding'] = \
        {'$ref': get_ref_for_pid('hold', 'toto')}
    templ_item_public_martigny['data']['organisation'] = \
        {'$ref': get_ref_for_pid('org', 'toto')}

    res, _ = postdata(
        client,
        post_entrypoint,
        templ_item_public_martigny
    )
    assert res.status_code == 201
    # ensure that added fields are removed from record.
    fields = [
        'barcode', 'pid', 'status', 'document', 'holding', 'organisation',
        'library']
    for field in fields:
        assert field not in res.json['metadata']['data']

    # templates now prevent the deletion of its owner
    assert system_librarian_martigny.get_links_to_me().get('templates')

    # test template creation for holdings
    del templ_hold_public_martigny['pid']
    # add fields that will be removed at the creation of the template.
    templ_hold_public_martigny['data']['pid'] = 'toto'
    templ_hold_public_martigny['data']['organisation'] = \
        {'$ref': get_ref_for_pid('org', 'toto')}
    templ_hold_public_martigny['data']['library'] = \
        {'$ref': get_ref_for_pid('lib', 'toto')}
    templ_hold_public_martigny['data']['document'] = \
        {'$ref': get_ref_for_pid('doc', 'toto')}

    res, _ = postdata(
        client,
        post_entrypoint,
        templ_hold_public_martigny
    )
    assert res.status_code == 201
    # ensure that added fields are removed from record.
    fields = ['organisation', 'library', 'document', 'pid']
    for field in fields:
        assert field not in res.json['metadata']['data']

    # test template creation for patrons
    del templ_patron_public_martigny['pid']
    # add fields that will be removed at the creation of the template.
    templ_patron_public_martigny['data']['pid'] = 'toto'
    templ_patron_public_martigny['data']['user_id'] = 'toto'
    templ_patron_public_martigny['data']['patron']['subscriptions'] = 'toto'
    templ_patron_public_martigny['data']['patron']['barcode'] = ['toto']

    res, _ = postdata(
        client,
        post_entrypoint,
        templ_patron_public_martigny
    )
    assert res.status_code == 201
    # ensure that added fields are removed from record.
    fields = ['user_id', 'patron.subscriptions', 'patron.barcode', 'pid']
    json_data = res.json['metadata']['data']
    for field in fields:
        if '.' in field:
            level_1, level_2 = field.split('.')
            assert level_2 not in json_data.get(level_1)
        else:
            assert field not in json_data

    # Sion
    login_user_via_session(client, system_librarian_sion.user)

    res, _ = postdata(
        client,
        post_entrypoint,
        templ_doc_public_martigny_data
    )
    assert res.status_code == 403


def test_template_secure_api_update(client,
                                    templ_doc_private_martigny,
                                    templ_doc_private_martigny_data,
                                    system_librarian_martigny,
                                    system_librarian_sion,
                                    librarian_martigny,
                                    librarian_saxon,
                                    json_header):
    """Test templates secure api update."""
    # Martigny
    login_user_via_session(client, system_librarian_martigny.user)
    record_url = url_for('invenio_records_rest.tmpl_item',
                         pid_value=templ_doc_private_martigny.pid)

    data = templ_doc_private_martigny_data
    data['name'] = 'Test Name'
    res = client.put(
        record_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 403

    login_user_via_session(client, librarian_martigny.user)
    data = templ_doc_private_martigny_data
    data['name'] = 'Test Name'
    data['data']['pid'] = 'toto'
    res = client.put(
        record_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 200
    # ensure that pid is removed from recordds
    assert 'pid' not in res.json['metadata']['data']

    data = templ_doc_private_martigny_data
    data['visibility'] = 'public'
    res = client.put(
        record_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 403

    login_user_via_session(client, system_librarian_martigny.user)
    data = templ_doc_private_martigny_data
    data['visibility'] = 'public'
    res = client.put(
        record_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 403

    login_user_via_session(client, librarian_saxon.user)
    data = templ_doc_private_martigny_data
    data['name'] = 'Test Name'
    res = client.put(
        record_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 403

    # Sion
    login_user_via_session(client, system_librarian_sion.user)
    res = client.put(
        record_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 403


def test_template_secure_api_delete(client,
                                    templ_doc_private_martigny,
                                    system_librarian_martigny,
                                    system_librarian_sion,
                                    templ_doc_public_martigny,
                                    librarian_saxon,
                                    librarian_martigny,
                                    json_header):
    """Test templates secure api delete."""
    record_url = url_for('invenio_records_rest.tmpl_item',
                         pid_value=templ_doc_private_martigny.pid)

    # Saxon
    login_user_via_session(client, librarian_saxon.user)
    res = client.delete(record_url)
    assert res.status_code == 403

    # Sion
    login_user_via_session(client, system_librarian_sion.user)
    res = client.delete(record_url)
    assert res.status_code == 403

    # Martigny
    login_user_via_session(client, system_librarian_martigny.user)
    res = client.delete(record_url)
    assert res.status_code == 403

    record_url = url_for('invenio_records_rest.tmpl_item',
                         pid_value=templ_doc_public_martigny.pid)

    # Martigny
    login_user_via_session(client, librarian_martigny.user)
    res = client.delete(record_url)
    assert res.status_code == 403

    login_user_via_session(client, system_librarian_martigny.user)
    res = client.delete(record_url)
    assert res.status_code == 204
