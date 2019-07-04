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

"""Tests REST API patrons."""

import json
from copy import deepcopy

import mock
import pytest
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import VerifyRecordPermissionPatch, get_json, to_relative_url

from rero_ils.modules.api import IlsRecordError
from rero_ils.modules.items.api import ItemStatus
from rero_ils.modules.loans.api import Loan, LoanAction
from rero_ils.modules.patrons.api import Patron
from rero_ils.modules.patrons.utils import user_has_patron


def test_patrons_shortcuts(
        client, librarian_martigny_no_email, patron_martigny_no_email,
        librarian_sion_no_email):
    """Test patron shortcuts."""
    new_patron = deepcopy(patron_martigny_no_email)
    assert new_patron.patron_type_pid
    assert new_patron.organisation_pid
    del new_patron['patron_type']
    assert not new_patron.patron_type_pid
    assert not new_patron.organisation_pid


def test_filtered_patrons_get(
        client, librarian_martigny_no_email, patron_martigny_no_email,
        librarian_sion_no_email):
    """Test patron filter by organisation."""
    # Martigny
    login_user_via_session(client, librarian_martigny_no_email.user)
    list_url = url_for('invenio_records_rest.ptrn_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total'] == 2

    # Sion
    # TODO: find why it's failed
    # login_user_via_session(client, librarian_sion_no_email.user)
    # list_url = url_for('invenio_records_rest.ptrn_list')

    # res = client.get(list_url)
    # assert res.status_code == 200
    # data = get_json(res)
    # assert data['hits']['total'] == 1


def test_patrons_permissions(client, librarian_martigny_no_email,
                             json_header):
    """Test record retrieval."""
    item_url = url_for(
        'invenio_records_rest.ptrn_item',
        pid_value=librarian_martigny_no_email.pid)
    post_url = url_for('invenio_records_rest.ptrn_list')

    res = client.get(item_url)
    assert res.status_code == 401

    res = client.post(
        post_url,
        data={},
        headers=json_header
    )
    assert res.status_code == 401

    res = client.put(
        item_url,
        data={},
        headers=json_header
    )

    res = client.delete(item_url)
    assert res.status_code == 401


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_patrons_get(client, librarian_martigny_no_email):
    """Test record retrieval."""
    patron = librarian_martigny_no_email
    item_url = url_for(
        'invenio_records_rest.ptrn_item',
        pid_value=librarian_martigny_no_email.pid)
    list_url = url_for(
        'invenio_records_rest.ptrn_list',
        q='pid:{pid}'.format(pid=librarian_martigny_no_email.pid))

    res = client.get(item_url)
    assert res.status_code == 200

    assert res.headers['ETag'] == '"{}"'.format(patron.revision_id)

    data = get_json(res)
    assert patron.dumps() == data['metadata']

    # Check metadata
    for k in ['created', 'updated', 'metadata', 'links']:
        assert k in data

    # Check self links
    res = client.get(to_relative_url(data['links']['self']))
    assert res.status_code == 200
    assert data == get_json(res)
    assert patron.dumps() == data['metadata']

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    result = data['hits']['hits'][0]['metadata']
    # organisation has been added during the indexing
    del(result['organisation'])
    assert result == patron.replace_refs()


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_patrons_post_put_delete(client, lib_martigny,
                                 patron_type_children_martigny,
                                 librarian_martigny_data, json_header,
                                 roles):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.ptrn_item', pid_value='1')
    post_url = url_for('invenio_records_rest.ptrn_list')
    list_url = url_for('invenio_records_rest.ptrn_list', q='pid:1')
    patron_data = librarian_martigny_data

    pids = len(Patron.get_all_pids())
    uuids = len(Patron.get_all_ids())

    # Create record / POST
    patron_data['pid'] = '1'
    patron_data['email'] = 'test@rero.ch'

    res = client.post(
        post_url,
        data=json.dumps(patron_data),
        headers=json_header
    )

    assert res.status_code == 201
    assert len(Patron.get_all_pids()) == pids + 1
    assert len(Patron.get_all_ids()) == uuids + 1

    # Check that the returned record matches the given data
    data = get_json(res)
    assert data['metadata'] == patron_data

    res = client.get(item_url)
    assert res.status_code == 200
    data = get_json(res)
    assert patron_data == data['metadata']

    # Update record/PUT
    data = patron_data
    data['first_name'] = 'Test Name'
    res = client.put(
        item_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 200
    # assert res.headers['ETag'] != '"{}"'.format(ptrnrarie.revision_id)

    # Check that the returned record matches the given data
    data = get_json(res)
    assert data['metadata']['first_name'] == 'Test Name'

    res = client.get(item_url)
    assert res.status_code == 200

    data = get_json(res)
    assert data['metadata']['first_name'] == 'Test Name'

    res = client.get(list_url)
    assert res.status_code == 200

    data = get_json(res)['hits']['hits'][0]
    assert data['metadata']['first_name'] == 'Test Name'

    # Delete record/DELETE
    res = client.delete(item_url)
    assert res.status_code == 204

    res = client.get(item_url)
    assert res.status_code == 410


def test_patron_secure_api(client, json_header,
                           librarian_martigny_no_email,
                           librarian_sion_no_email):
    """Test patron type secure api access."""
    # Martigny
    login_user_via_session(client, librarian_martigny_no_email.user)
    record_url = url_for('invenio_records_rest.ptrn_item',
                         pid_value=librarian_martigny_no_email.pid)

    res = client.get(record_url)
    assert res.status_code == 200

    # Sion
    # TODO: find why it's failed
    # login_user_via_session(client, librarian_sion_no_email.user)
    # record_url = url_for('invenio_records_rest.ptrn_item',
    #                      pid_value=librarian_martigny_no_email.pid)

    # res = client.get(record_url)
    # assert res.status_code == 403


def test_patron_secure_api_create(client, json_header,
                                  patron_martigny_data,
                                  librarian_martigny_no_email,
                                  librarian_sion_no_email):
    """Test patron secure api create."""
    # Martigny
    login_user_via_session(client, librarian_martigny_no_email.user)
    post_url = url_for('invenio_records_rest.ptrn_list')

    del patron_martigny_data['pid']
    res = client.post(
        post_url,
        data=json.dumps(patron_martigny_data),
        headers=json_header
    )
    assert res.status_code == 201

    # # Sion
    # login_user_via_session(client, librarian_sion_no_email.user)

    # res = client.post(
    #     post_url,
    #     data=json.dumps(patron_martigny_data),
    #     headers=json_header
    # )
    # assert res.status_code == 403


def test_patron_secure_api_update(client, json_header,
                                  patron_martigny_data,
                                  librarian_martigny_no_email,
                                  librarian_sion_no_email,
                                  patron_martigny):
    """Test patron secure api update."""
    login_user_via_session(client, librarian_martigny_no_email.user)
    record_url = url_for('invenio_records_rest.ptrn_item',
                         pid_value=patron_martigny.pid)

    data = patron_martigny_data
    data['first_name'] = 'New Name'
    res = client.put(
        record_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 200

    # Sion
    # login_user_via_session(client, librarian_sion_no_email.user)

    # res = client.put(
    #     record_url,
    #     data=json.dumps(data),
    #     headers=json_header
    # )
    # assert res.status_code == 403


def test_patron_secure_api_delete(client, json_header,
                                  patron_martigny_data,
                                  librarian_martigny_no_email,
                                  librarian_sion_no_email,
                                  patron_martigny):
    """Test patron secure api delete."""
    login_user_via_session(client, librarian_martigny_no_email.user)
    record_url = url_for('invenio_records_rest.ptrn_item',
                         pid_value=patron_martigny.pid)

    res = client.delete(record_url)
    assert res.status_code == 204

    # Sion
    # login_user_via_session(client, librarian_sion_no_email.user)

    # res = client.delete(record_url)
    # assert res.status_code == 403
