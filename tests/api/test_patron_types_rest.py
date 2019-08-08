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

"""Tests REST API patron types."""

import json

import mock
import pytest
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import VerifyRecordPermissionPatch, get_json, to_relative_url

from rero_ils.modules.api import IlsRecordError


def test_patron_types_permissions(client, patron_type_children_martigny,
                                  json_header):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.ptty_item', pid_value='ptty1')
    post_url = url_for('invenio_records_rest.ptty_list')

    res = client.get(item_url)
    assert res.status_code == 401

    res = client.post(
        post_url,
        data={},
        headers=json_header
    )
    assert res.status_code == 401

    res = client.put(
        url_for('invenio_records_rest.ptty_item', pid_value='ptty1'),
        data={},
        headers=json_header
    )

    res = client.delete(item_url)
    assert res.status_code == 401

    res = client.get(url_for('patron_types.name_validate', name='standard'))
    assert res.status_code == 401


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_patron_types_get(client, patron_type_children_martigny):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.ptty_item', pid_value='ptty1')
    patron_type = patron_type_children_martigny
    res = client.get(item_url)
    assert res.status_code == 200

    assert res.headers['ETag'] == '"{}"'.format(patron_type.revision_id)

    data = get_json(res)
    assert patron_type.dumps() == data['metadata']

    # Check metadata
    for k in ['created', 'updated', 'metadata', 'links']:
        assert k in data

    # Check self links
    res = client.get(to_relative_url(data['links']['self']))
    assert res.status_code == 200
    assert data == get_json(res)
    assert patron_type.dumps() == data['metadata']

    list_url = url_for('invenio_records_rest.ptty_list', pid='ptty1')
    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)

    assert data['hits']['hits'][0]['metadata'] == patron_type.replace_refs()


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_patron_types_post_put_delete(client, org_martigny,
                                      patron_type_children_martigny_data,
                                      json_header):
    """Test record retrieval."""
    # Create record / POST
    item_url = url_for('invenio_records_rest.ptty_item', pid_value='1')
    post_url = url_for('invenio_records_rest.ptty_list')
    list_url = url_for('invenio_records_rest.ptty_list', q='pid:1')

    patron_type_children_martigny_data['pid'] = '1'
    res = client.post(
        post_url,
        data=json.dumps(patron_type_children_martigny_data),
        headers=json_header
    )
    assert res.status_code == 201

    # Check that the returned record matches the given data
    data = get_json(res)
    assert data['metadata'] == patron_type_children_martigny_data

    res = client.get(item_url)
    assert res.status_code == 200
    data = get_json(res)
    assert patron_type_children_martigny_data == data['metadata']

    # Update record/PUT
    data = patron_type_children_martigny_data
    data['name'] = 'Test Name'
    res = client.put(
        item_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 200
    # assert res.headers['ETag'] != '"{}"'.format(librarie.revision_id)

    # Check that the returned record matches the given data
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

    # Delete record/DELETE
    res = client.delete(item_url)
    assert res.status_code == 204

    res = client.get(item_url)
    assert res.status_code == 410


@mock.patch('rero_ils.modules.patron_types.views.login_and_librarian',
            mock.MagicMock())
def test_patron_types_name_validate(client, patron_type_children_martigny):
    """Test patron type name validation."""

    url = url_for('patron_types.name_validate', name='children')

    class current_patron:
        class organisation:
            pid = 'org1'
    with mock.patch(
        'rero_ils.modules.patron_types.views.current_patron',
        current_patron
    ):
        res = client.get(url)
        assert res.status_code == 200
        assert get_json(res) == {'name': 'children'}

    class current_patron:
        class organisation:
            pid = 'does not exists'
    with mock.patch(
        'rero_ils.modules.patron_types.views.current_patron',
        current_patron
    ):
        res = client.get(url)
        assert res.status_code == 200
        assert get_json(res) == {'name': None}


def test_patron_types_can_delete(client, patron_type_children_martigny,
                                 patron_martigny_no_email,
                                 circulation_policies):
    """Test can delete a patron type."""
    patron_type = patron_type_children_martigny
    links = patron_type.get_links_to_me()
    assert 'circ_policies' in links
    assert 'patrons' in links

    assert not patron_type.can_delete

    reasons = patron_type.reasons_not_to_delete()
    assert 'links' in reasons


def test_filtered_patron_types_get(
        client, librarian_martigny_no_email, patron_type_children_martigny,
        patron_type_adults_martigny, librarian_sion_no_email,
        patron_type_youngsters_sion, patron_type_grown_sion):
    """Test patron types filter by organisation."""
    # Martigny
    login_user_via_session(client, librarian_martigny_no_email.user)
    list_url = url_for('invenio_records_rest.ptty_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total'] == 2

    # Sion
    login_user_via_session(client, librarian_sion_no_email.user)
    list_url = url_for('invenio_records_rest.ptty_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total'] == 2


def test_patron_type_secure_api(client, json_header,
                                patron_type_children_martigny,
                                librarian_martigny_no_email,
                                librarian_sion_no_email):
    """Test patron type secure api access."""
    # Martigny
    login_user_via_session(client, librarian_martigny_no_email.user)
    record_url = url_for('invenio_records_rest.ptty_item',
                         pid_value=patron_type_children_martigny.pid)

    res = client.get(record_url)
    assert res.status_code == 200

    # Sion
    login_user_via_session(client, librarian_sion_no_email.user)
    record_url = url_for('invenio_records_rest.ptty_item',
                         pid_value=patron_type_children_martigny.pid)

    res = client.get(record_url)
    assert res.status_code == 403


def test_patron_type_secure_api_create(client, json_header,
                                       patron_type_children_martigny,
                                       librarian_martigny_no_email,
                                       librarian_sion_no_email,
                                       patron_type_children_martigny_data):
    """Test patron type secure api create."""
    # Martigny
    login_user_via_session(client, librarian_martigny_no_email.user)
    post_url = url_for('invenio_records_rest.ptty_list')

    del patron_type_children_martigny_data['pid']
    res = client.post(
        post_url,
        data=json.dumps(patron_type_children_martigny_data),
        headers=json_header
    )
    assert res.status_code == 201

    # Sion
    login_user_via_session(client, librarian_sion_no_email.user)

    res = client.post(
        post_url,
        data=json.dumps(patron_type_children_martigny_data),
        headers=json_header
    )
    assert res.status_code == 403


def test_patron_type_secure_api_update(client, json_header,
                                       patron_type_adults_martigny,
                                       librarian_martigny_no_email,
                                       librarian_sion_no_email,
                                       patron_type_adults_martigny_data):
    """Test patron type secure api create."""
    login_user_via_session(client, librarian_martigny_no_email.user)
    record_url = url_for('invenio_records_rest.ptty_item',
                         pid_value=patron_type_adults_martigny.pid)

    data = patron_type_adults_martigny_data
    data['name'] = 'New Name'
    res = client.put(
        record_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 200

    # Sion
    login_user_via_session(client, librarian_sion_no_email.user)

    res = client.put(
        record_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 403


def test_patron_type_secure_api_delete(client, json_header,
                                       patron_type_adults_martigny,
                                       librarian_martigny_no_email,
                                       librarian_sion_no_email,
                                       patron_type_adults_martigny_data):
    """Test patron type secure api delete."""
    login_user_via_session(client, librarian_martigny_no_email.user)
    record_url = url_for('invenio_records_rest.ptty_item',
                         pid_value=patron_type_adults_martigny.pid)

    with pytest.raises(IlsRecordError.NotDeleted):
        res = client.delete(record_url)
        assert res.status_code == 204

    # Sion
    login_user_via_session(client, librarian_sion_no_email.user)

    res = client.delete(record_url)
    assert res.status_code == 403
