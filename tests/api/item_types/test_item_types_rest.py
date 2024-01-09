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

"""Tests REST API item types."""

import json

import mock
import pytest
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import VerifyRecordPermissionPatch, get_json, postdata, \
    to_relative_url

from rero_ils.modules.api import IlsRecordError


def test_item_types_permissions(client, item_type_standard_martigny,
                                json_header):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.itty_item', pid_value='itty1')

    res = client.get(item_url)
    assert res.status_code == 401

    res, _ = postdata(
        client,
        'invenio_records_rest.itty_list',
        {}
    )
    assert res.status_code == 401

    res = client.put(
        url_for('invenio_records_rest.itty_item', pid_value='itty1'),
        data={},
        headers=json_header
    )
    assert res.status_code == 401

    res = client.delete(item_url)
    assert res.status_code == 401

    res = client.get(url_for('item_types.name_validate', name='standard'))
    assert res.status_code == 401


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_item_types_get(client, item_type_standard_martigny):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.itty_item', pid_value='itty1')
    item_type = item_type_standard_martigny
    res = client.get(item_url)
    assert res.status_code == 200

    assert res.headers['ETag'] == f'"{item_type.revision_id}"'

    data = get_json(res)
    assert item_type.dumps() == data['metadata']

    # Check metadata
    for k in ['created', 'updated', 'metadata', 'links']:
        assert k in data

    # Check self links
    res = client.get(to_relative_url(data['links']['self']))
    assert res.status_code == 200
    assert data == get_json(res)
    assert item_type.dumps() == data['metadata']

    list_url = url_for('invenio_records_rest.itty_list', pid='itty1')
    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)

    assert data['hits']['hits'][0]['metadata'] == item_type.replace_refs()


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_item_types_post_put_delete(client, org_martigny,
                                    item_type_standard_martigny_data,
                                    json_header):
    """Test record retrieval."""
    # Create record / POST
    item_url = url_for('invenio_records_rest.itty_item', pid_value='1')
    list_url = url_for('invenio_records_rest.itty_list', q='pid:1')

    item_type_standard_martigny_data['pid'] = '1'
    res, data = postdata(
        client,
        'invenio_records_rest.itty_list',
        item_type_standard_martigny_data
    )
    assert res.status_code == 201

    # Check that the returned record matches the given data
    assert data['metadata'] == item_type_standard_martigny_data

    res = client.get(item_url)
    assert res.status_code == 200
    data = get_json(res)
    assert item_type_standard_martigny_data == data['metadata']

    # Update record/PUT
    data = item_type_standard_martigny_data
    data['name'] = 'Test Name'
    res = client.put(
        item_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 200
    # assert res.headers['ETag'] != f'"{librarie.revision_id}"'

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


@mock.patch('rero_ils.modules.decorators.login_and_librarian',
            mock.MagicMock())
def test_item_types_name_validate(client):
    """Test record name validation."""
    url = url_for('item_types.name_validate', name='standard')

    class current_librarian:
        class organisation:
            pid = 'org1'
    with mock.patch(
        'rero_ils.modules.item_types.views.current_librarian',
        current_librarian
    ):
        res = client.get(url)
        assert res.status_code == 200
        assert get_json(res) == {'name': 'standard'}

    class current_librarian:
        class organisation:
            pid = 'does not exists'
    with mock.patch(
        'rero_ils.modules.item_types.views.current_librarian',
        current_librarian
    ):
        res = client.get(url)
        assert res.status_code == 200
        assert get_json(res) == {'name': None}


def test_item_types_can_delete(client, item_type_standard_martigny,
                               item_lib_martigny,
                               circulation_policies):
    """Test can delete an item type."""
    can, reasons = item_type_standard_martigny.can_delete
    assert not can
    assert reasons['links']['circ_policies']
    assert reasons['links']['items']


def test_filtered_item_types_get(
        client, librarian_martigny, item_type_standard_martigny,
        item_type_on_site_martigny, item_type_specific_martigny,
        librarian_sion, item_type_regular_sion,
        item_type_internal_sion, item_type_particular_sion):
    """Test item types filter by organisation."""
    # Martigny
    login_user_via_session(client, librarian_martigny.user)
    list_url = url_for('invenio_records_rest.itty_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total']['value'] == 4

    # Sion
    login_user_via_session(client, librarian_sion.user)
    list_url = url_for('invenio_records_rest.itty_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total']['value'] == 4


def test_item_type_secure_api(client, json_header,
                              item_type_standard_martigny,
                              librarian_martigny,
                              librarian_sion):
    """Test item type secure api access."""
    # Martigny
    login_user_via_session(client, librarian_martigny.user)
    record_url = url_for('invenio_records_rest.itty_item',
                         pid_value=item_type_standard_martigny.pid)

    res = client.get(record_url)
    assert res.status_code == 200

    # Sion
    login_user_via_session(client, librarian_sion.user)
    record_url = url_for('invenio_records_rest.itty_item',
                         pid_value=item_type_standard_martigny.pid)

    res = client.get(record_url)
    assert res.status_code == 403


def test_item_type_secure_api_create(client, json_header,
                                     item_type_standard_martigny,
                                     system_librarian_martigny,
                                     system_librarian_sion,
                                     item_type_standard_martigny_data):
    """Test item type secure api create."""
    # Martigny
    login_user_via_session(client, system_librarian_martigny.user)
    post_entrypoint = 'invenio_records_rest.itty_list'

    del item_type_standard_martigny_data['pid']
    res, _ = postdata(
        client,
        post_entrypoint,
        item_type_standard_martigny_data
    )
    assert res.status_code == 201

    # Sion
    login_user_via_session(client, system_librarian_sion.user)

    res, _ = postdata(
        client,
        post_entrypoint,
        item_type_standard_martigny_data
    )
    assert res.status_code == 403


def test_item_type_secure_api_update(client,
                                     item_type_on_site_martigny,
                                     system_librarian_martigny,
                                     system_librarian_sion,
                                     item_type_on_site_martigny_data,
                                     json_header):
    """Test item type secure api update."""
    # Martigny
    login_user_via_session(client, system_librarian_martigny.user)
    record_url = url_for('invenio_records_rest.itty_item',
                         pid_value=item_type_on_site_martigny.pid)

    data = item_type_on_site_martigny
    data['name'] = 'Test Name'
    res = client.put(
        record_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 200

    # Sion
    login_user_via_session(client, system_librarian_sion.user)

    res = client.put(
        record_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 403


def test_item_type_secure_api_delete(client,
                                     item_type_on_site_martigny,
                                     system_librarian_martigny,
                                     system_librarian_sion,
                                     item_type_on_site_martigny_data,
                                     json_header):
    """Test item type secure api delete."""
    # Martigny
    login_user_via_session(client, system_librarian_martigny.user)
    record_url = url_for('invenio_records_rest.itty_item',
                         pid_value=item_type_on_site_martigny.pid)

    with pytest.raises(IlsRecordError.NotDeleted):
        res = client.delete(record_url)
        assert res.status_code == 200

    # Sion
    login_user_via_session(client, system_librarian_sion.user)

    res = client.delete(record_url)
    assert res.status_code == 403
