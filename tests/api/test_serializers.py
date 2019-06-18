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
