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

"""Tests REST API patrons."""

import json
from copy import deepcopy

import mock
from flask import url_for
from invenio_access import Permission
from invenio_accounts.testutils import login_user_via_session
from utils import get_json, postdata

from rero_ils.permissions import librarian_delete_permission_factory, \
    user_has_roles


def test_librarian_delete_permission_factory(
        client, librarian_fully_no_email, org_martigny, lib_martigny):
    """Test librarian_delete_permission_factory """
    login_user_via_session(client, librarian_fully_no_email.user)
    assert type(
        librarian_delete_permission_factory(None, credentials_only=True)
    ) == Permission
    assert librarian_delete_permission_factory(org_martigny) is not None


def test_librarian_permissions(
        client, system_librarian_martigny_no_email, json_header,
        patron_martigny_no_email,
        librarian_fully_no_email,
        patron_martigny_data_tmp,
        lib_saxon):
    """Test librarian permissions."""
    # Login as librarian
    login_user_via_session(client, librarian_fully_no_email.user)

    record = {
        "$schema": "https://ils.rero.ch/schemas/patrons/patron-v0.0.1.json",
        "first_name": "first_name",
        "last_name": "Last_name",
        "street": "Avenue Leopold-Robert, 132",
        "postal_code": "1920",
        "city": "Martigny",
        "birth_date": "1967-06-07",
        "patron_type": {"$ref": "https://ils.rero.ch/api/patron_types/ptty1"},
        "library": {"$ref": "https://ils.rero.ch/api/libraries/lib1"},
        "phone": "+41324993111"
    }

    # can retrieve all type of users.
    list_url = url_for('invenio_records_rest.ptrn_list')
    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total']['value'] == 3

    # can manage all types of patron roles
    role_url = url_for('api_patrons.get_roles_management_permissions')
    res = client.get(role_url)
    assert res.status_code == 200
    data = get_json(res)
    assert 'librarian' in data['allowed_roles']
    assert 'system_librarian' not in data['allowed_roles']

    # can create all type of users except system_librarians
    post_entrypoint = 'invenio_records_rest.ptrn_list'
    system_librarian = deepcopy(record)
    librarian = deepcopy(record)
    librarian_saxon = deepcopy(record)
    librarian_saxon['library'] = \
        {"$ref": "https://ils.rero.ch/api/libraries/lib2"}
    librarian['library'] = \
        {"$ref": "https://ils.rero.ch/api/libraries/lib3"}
    patron = deepcopy(record)
    patron['library'] = \
        {"$ref": "https://ils.rero.ch/api/libraries/lib3"}
    counter = 1
    for record in [
        {'data': patron, 'role': 'patron'},
        {'data': librarian, 'role': 'librarian'},
    ]:
        counter += 1
        data = record['data']
        data['roles'] = [record['role']]
        data['barcode'] = 'barcode' + str(counter)
        data['email'] = str(counter) + '@domain.com'
        with mock.patch('rero_ils.modules.patrons.api.'
                        'send_reset_password_instructions'):
            res, _ = postdata(
                client,
                post_entrypoint,
                data
            )
            assert res.status_code == 201
            user = get_json(res)['metadata']
            user_pid = user.get('pid')
            record_url = url_for('invenio_records_rest.ptrn_item',
                                 pid_value=user_pid)
            res = client.get(record_url)
            assert res.status_code == 200
            user = get_json(res)['metadata']

    # can update all type of user records except system_librarian.
            user['first_name'] = 'New Name' + str(counter)
            res = client.put(
                record_url,
                data=json.dumps(user),
                headers=json_header
            )
            assert res.status_code == 200

    # can not add the role system_librarian to user
            user['roles'] = ['system_librarian']
            res = client.put(
                record_url,
                data=json.dumps(user),
                headers=json_header
            )
            assert res.status_code == 403

    # can delete all type of user records except system_librarian.
            record_url = url_for('invenio_records_rest.ptrn_item',
                                 pid_value=user_pid)

            res = client.delete(record_url)
            assert res.status_code == 204

    # can not create librarians of same libray.
    counter = 1
    for record in [
        {'data': librarian_saxon, 'role': 'librarian'},
    ]:
        counter += 1
        data = record['data']
        data['roles'] = [record['role']]
        data['barcode'] = 'barcode' + str(counter)
        data['email'] = str(counter) + '@domain.com'
        with mock.patch('rero_ils.modules.patrons.api.'
                        'send_reset_password_instructions'):
            res, _ = postdata(
                client,
                post_entrypoint,
                data
            )
            assert res.status_code == 403

    system_librarian['roles'] = ['system_librarian']
    system_librarian['barcode'] = 'barcode'
    system_librarian['email'] = '4@domain.com'
    with mock.patch('rero_ils.modules.patrons.api.'
                    'send_reset_password_instructions'):
        res, _ = postdata(
            client,
            post_entrypoint,
            system_librarian,
        )
        assert res.status_code == 403

    # can update all type of user records except system_librarian.
    record_url = url_for('invenio_records_rest.ptrn_item',
                         pid_value=system_librarian_martigny_no_email.pid)
    system_librarian_martigny_no_email['first_name'] = 'New Name'
    res = client.put(
        record_url,
        data=json.dumps(system_librarian_martigny_no_email),
        headers=json_header
    )
    assert res.status_code == 403

    # can delete all type of user records except system_librarian.
    sys_librarian_pid = system_librarian_martigny_no_email.get('pid')
    record_url = url_for('invenio_records_rest.ptrn_item',
                         pid_value=sys_librarian_pid)

    res = client.delete(record_url)
    assert res.status_code == 403


def test_user_has_roles(system_librarian_martigny_no_email,
                        librarian_martigny_no_email):
    """Test if user has roles permissions."""
    with mock.patch('rero_ils.permissions.current_user',
                    librarian_martigny_no_email.user):
        assert user_has_roles(None, roles=['system_librarian', 'librarian'],
                              condition='or')

    assert user_has_roles(system_librarian_martigny_no_email.user,
                          roles=['system_librarian', 'librarian'],
                          condition='and')
    assert user_has_roles(librarian_martigny_no_email.user,
                          roles=['system_librarian', 'librarian'],
                          condition='or')
    assert user_has_roles(librarian_martigny_no_email.user,
                          roles=['system_librarian', 'librarian'],
                          condition='and') is False
