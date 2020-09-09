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
from invenio_accounts.testutils import login_user_via_session
from utils import get_json, postdata


def test_system_librarian_permissions(
        client, json_header, system_librarian_martigny_no_email,
        patron_martigny_no_email, patron_type_adults_martigny,
        librarian_fully_no_email):
    """Test system_librarian permissions."""
    # Login as system_librarian
    login_user_via_session(client, system_librarian_martigny_no_email.user)

    record = {
        "$schema": "https://ils.rero.ch/schemas/patrons/patron-v0.0.1.json",
        "first_name": "first_name",
        "last_name": "Last_name",
        "username": "user",
        "street": "Avenue Leopold-Robert, 132",
        "postal_code": "1920",
        "city": "Martigny",
        "birth_date": "1967-06-07",
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
    assert 'system_librarian' in data['allowed_roles']

    # can create all type of users.
    system_librarian = deepcopy(record)
    librarian = deepcopy(record)
    patron = deepcopy(record)
    counter = 1
    records = [{
        'data': patron, 'role': ['patron'], 'patron_type': {
            '$ref': 'https://ils.rero.ch/api/patron_types/ptty2'
        }
    }, {
        'data': librarian, 'role': ['librarian'], 'library': {
            '$ref': 'https://ils.rero.ch/api/libraries/lib1'
        }
    }, {
        'data': system_librarian, 'role': [
            'librarian', 'system_librarian'
        ], 'library': {
            '$ref': 'https://ils.rero.ch/api/libraries/lib1'
        }
    }]
    for record in records:
        counter += 1
        data = record['data']
        data['roles'] = record['role']
        data['barcode'] = 'barcode' + str(counter)
        data['email'] = str(counter) + '@domain.com'
        data['username'] = 'user' + str(counter)
        if record.get('patron_type'):
            data['patron_type'] = record['patron_type']
        if record.get('library'):
            data['library'] = record['library']
        with mock.patch('rero_ils.modules.patrons.api.'
                        'send_reset_password_instructions'):
            res, _ = postdata(
                client,
                'invenio_records_rest.ptrn_list',
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

    # can update all type of user records.
            user['first_name'] = 'New Name' + str(counter)
            res = client.put(
                record_url,
                data=json.dumps(user),
                headers=json_header
            )
            assert res.status_code == 200

    # can delete all type of user records.
            record_url = url_for('invenio_records_rest.ptrn_item',
                                 pid_value=user_pid)

            res = client.delete(record_url)
            assert res.status_code == 204
