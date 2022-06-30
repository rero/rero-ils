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

from flask import url_for
from invenio_access import Permission
from invenio_accounts.testutils import login_user_via_session
from utils import get_json, postdata

from rero_ils.modules.users.models import UserRole
from rero_ils.permissions import librarian_delete_permission_factory
from rero_ils.utils import create_user_from_data


def test_librarian_delete_permission_factory(
        client, librarian_fully, org_martigny, lib_martigny):
    """Test librarian_delete_permission_factory """
    login_user_via_session(client, librarian_fully.user)
    assert type(
        librarian_delete_permission_factory(None, credentials_only=True)
    ) == Permission
    assert librarian_delete_permission_factory(org_martigny) is not None


def test_librarian_permissions(
        client, system_librarian_martigny, json_header,
        patron_martigny,
        librarian_fully,
        patron_martigny_data_tmp,
        lib_saxon):
    """Test librarian permissions."""
    # Login as librarian
    login_user_via_session(client, librarian_fully.user)

    record = {
        "$schema": "https://bib.rero.ch/schemas/patrons/patron-v0.0.1.json",
        "first_name": "first_name",
        "last_name": "Last_name",
        "username": "username",
        "street": "Avenue Leopold-Robert, 132",
        "postal_code": "1920",
        "city": "Martigny",
        "birth_date": "1967-06-07",
        "patron": {
            "expiration_date": "2023-10-07",
            "type": {"$ref": "https://bib.rero.ch/api/patron_types/ptty1"},
            "communication_channel": "mail",
            "communication_language": "ita"
        },
        "libraries": [{"$ref": "https://bib.rero.ch/api/libraries/lib1"}],
        "home_phone": "+41324993111"
    }
    record = create_user_from_data(record)
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
    assert all(r in data['allowed_roles'] for r in UserRole.LIBRARIAN_ROLES)
    assert UserRole.FULL_PERMISSIONS not in data['allowed_roles']

    # can create all type of users except system_librarians
    post_entrypoint = 'invenio_records_rest.ptrn_list'
    system_librarian = deepcopy(record)
    librarian = deepcopy(record)
    librarian_saxon = deepcopy(record)
    librarian_saxon['libraries'] = \
        [{"$ref": "https://bib.rero.ch/api/libraries/lib2"}]
    librarian['libraries'] = \
        [{"$ref": "https://bib.rero.ch/api/libraries/lib3"}]
    patron = deepcopy(record)
    patron['libraries'] = \
        [{"$ref": "https://bib.rero.ch/api/libraries/lib3"}]
    for counter, record in enumerate([
        {'data': patron, 'role': [UserRole.PATRON]},
        {'data': librarian, 'role': UserRole.LIBRARIAN_ROLES},
    ]):
        data = record['data']
        data['roles'] = record['role']
        data['patron']['barcode'] = [f'barcode{str(counter)}']
        res, _ = postdata(client, post_entrypoint, data)
        assert res.status_code == 201
        user = get_json(res)['metadata']
        user_pid = user.get('pid')
        record_url = url_for('invenio_records_rest.ptrn_item',
                             pid_value=user_pid)
        res = client.get(record_url)
        assert res.status_code == 200
        user = get_json(res)['metadata']

        # can update all type of user records except system_librarian.
        user['first_name'] = f'New Name{str(counter)}'
        res = client.put(
            record_url,
            data=json.dumps(user),
            headers=json_header
        )
        assert res.status_code == 200

        # can not add the role FULL_PERMISSIONS to user
        user['roles'] = [UserRole.FULL_PERMISSIONS]
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

    data = librarian_saxon
    data['roles'] = UserRole.LIBRARIAN_ROLES
    data['patron']['barcode'] = ['barcode#1']
    res, _ = postdata(client, post_entrypoint, data)
    assert res.status_code == 403

    system_librarian['roles'] = [UserRole.FULL_PERMISSIONS]
    system_librarian['patron']['barcode'] = ['barcode']

    res, _ = postdata(
        client,
        post_entrypoint,
        system_librarian,
    )
    assert res.status_code == 403

    # can update all type of user records except system_librarian.
    record_url = url_for('invenio_records_rest.ptrn_item',
                         pid_value=system_librarian_martigny.pid)
    system_librarian_martigny['first_name'] = 'New Name'
    res = client.put(
        record_url,
        data=json.dumps(system_librarian_martigny),
        headers=json_header
    )
    assert res.status_code == 403

    # can delete all type of user records except system_librarian.
    sys_librarian_pid = system_librarian_martigny.get('pid')
    record_url = url_for('invenio_records_rest.ptrn_item',
                         pid_value=sys_librarian_pid)

    res = client.delete(record_url)
    assert res.status_code == 403
