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

"""Tests Serializers."""


import mock
from flask import url_for
from utils import VerifyRecordPermissionPatch, get_json, login_user


def test_patrons_serializers(
    client,
    json_header,
    patron_martigny_no_email,
    librarian_martigny_no_email,
    librarian2_martigny_no_email,
    librarian_saxon_no_email,
    system_librarian_martigny_no_email,
    system_librarian_sion_no_email,
    librarian_sion_no_email
):
    """Test serializers for patrons."""

    # simple librarian
    login_user(client, librarian_martigny_no_email)

    # should update and delete a librarian of the same library
    item_url = url_for(
        'invenio_records_rest.ptrn_item',
        pid_value=librarian2_martigny_no_email.pid)

    response = client.get(item_url, headers=json_header)
    assert response.status_code == 200
    data = get_json(response)
    assert 'cannot_delete' not in data['permissions']
    assert 'cannot_update' not in data['permissions']
    assert data['links']['update']
    assert data['links']['delete']

    # should not update and delete a librarian of an other library
    item_url = url_for(
        'invenio_records_rest.ptrn_item',
        pid_value=librarian_saxon_no_email.pid)
    response = client.get(item_url, headers=json_header)
    assert response.status_code == 200
    assert 'cannot_delete' in get_json(response)['permissions']
    assert 'cannot_update' in get_json(response)['permissions']

    # should not update and delete a system librarian
    item_url = url_for(
        'invenio_records_rest.ptrn_item',
        pid_value=system_librarian_martigny_no_email.pid)
    response = client.get(item_url, headers=json_header)
    assert response.status_code == 200
    assert 'cannot_delete' in get_json(response)['permissions']
    assert 'cannot_update' in get_json(response)['permissions']

    # simple librarian
    login_user(client, system_librarian_martigny_no_email)
    # should update and delete a librarian of the same library
    item_url = url_for(
        'invenio_records_rest.ptrn_item',
        pid_value=librarian2_martigny_no_email.pid)
    response = client.get(item_url, headers=json_header)
    assert response.status_code == 200
    assert 'cannot_delete' not in get_json(response)['permissions']
    assert 'cannot_update' not in get_json(response)['permissions']

    # should update and delete a librarian of an other library
    item_url = url_for(
        'invenio_records_rest.ptrn_item',
        pid_value=librarian_saxon_no_email.pid)
    response = client.get(item_url, headers=json_header)
    assert response.status_code == 200
    assert 'cannot_delete' not in get_json(response)['permissions']
    assert 'cannot_update' not in get_json(response)['permissions']

    # should update and delete a system librarian of the same organistion
    item_url = url_for(
        'invenio_records_rest.ptrn_item',
        pid_value=system_librarian_martigny_no_email.pid)
    response = client.get(item_url, headers=json_header)
    assert response.status_code == 200
    assert 'cannot_delete' not in get_json(response)['permissions']
    assert 'cannot_update' not in get_json(response)['permissions']

    # should not update and delete a system librarian of an other organisation
    item_url = url_for(
        'invenio_records_rest.ptrn_item',
        pid_value=system_librarian_martigny_no_email.pid)
    response = client.get(item_url, headers=json_header)
    assert response.status_code == 200
    assert 'cannot_delete' not in get_json(response)['permissions']
    assert 'cannot_update' not in get_json(response)['permissions']

    list_url = url_for(
        'invenio_records_rest.ptrn_list')

    response = client.get(list_url, headers=json_header)
    assert response.status_code == 200
    data = get_json(response)


def test_items_serializers(
    client,
    item_lib_martigny,  # on shelf
    item_lib_fully,  # on loan
    json_header,
    patron_martigny_no_email,
    librarian_martigny_no_email,
    librarian_sion_no_email,
    loan_pending_martigny
):
    """Test record retrieval."""
    login_user(client, librarian_martigny_no_email)

    item_url = url_for(
        'invenio_records_rest.item_item', pid_value=item_lib_fully.pid)
    response = client.get(item_url, headers=json_header)
    assert response.status_code == 200
    data = get_json(response)
    assert 'cannot_delete' in data['permissions']
    assert 'cannot_update' not in data['permissions']
    assert data['metadata'].get('item_type').get('$ref')

    item_url = url_for(
        'invenio_records_rest.item_item',
        pid_value=item_lib_fully.pid, resolve=1)
    response = client.get(item_url, headers=json_header)
    data = get_json(response)['metadata']
    assert data.get('item_type').get('pid')
