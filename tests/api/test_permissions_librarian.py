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
from rero_ils.modules.patrons.utils import user_has_patron


def test_librarian_permissions(
        client, system_librarian_martigny_no_email, json_header,
        patron_martigny_no_email,
        librarian_only_fully_no_email,
        patron_martigny_data_tmp,
        lib_saxon):
    """Test librarian permissions."""
    # Login as librarian
    login_user_via_session(client, librarian_only_fully_no_email.user)

    record = {
        "$schema": "https://ils.rero.ch/schema/patrons/patron-v0.0.1.json",
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
    assert data['hits']['total'] == 3

    # can create all type of users except system_librarians
    post_url = url_for('invenio_records_rest.ptrn_list')
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
            res = client.post(
                post_url,
                data=json.dumps(data),
                headers=json_header
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
            res = client.post(
                post_url,
                data=json.dumps(data),
                headers=json_header
            )
            assert res.status_code == 403

    system_librarian['roles'] = ['system_librarian']
    system_librarian['barcode'] = 'barcode'
    system_librarian['email'] = '4@domain.com'
    with mock.patch('rero_ils.modules.patrons.api.'
                    'send_reset_password_instructions'):
        res = client.post(
            post_url,
            data=json.dumps(system_librarian),
            headers=json_header
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
