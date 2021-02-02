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

from copy import deepcopy

from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import postdata

from rero_ils.permissions import staffer_is_authenticated


def test_anonymous_user():
    """Test functions if not logged."""
    assert not staffer_is_authenticated()


def test_patron_permissions(
        client, json_header, system_librarian_martigny,
        patron_martigny,
        librarian_fully):
    """Test patron permissions."""
    # Login as patron
    login_user_via_session(client, patron_martigny.user)

    record = {
        "$schema": "https://ils.rero.ch/schemas/patrons/patron-v0.0.1.json",
        "first_name": "first_name",
        "last_name": "Last_name",
        "street": "Avenue Leopold-Robert, 132",
        "postal_code": "1920",
        "city": "Martigny",
        "birth_date": "1967-06-07",
        "patron": {
            "expiration_date": "2023-10-07",
            "type": {"$ref": "https://ils.rero.ch/api/patron_types/ptty1"},
            "communication_channel": "email",
            "communication_language": "ita"
        },
        "phone": "+41324993111"
    }

    # can not retrieve any type of users.
    list_url = url_for('invenio_records_rest.ptrn_list')
    res = client.get(list_url)
    assert res.status_code == 403

    # can not manage any types of patron roles
    role_url = url_for('api_patrons.get_roles_management_permissions')
    res = client.get(role_url)
    assert res.status_code == 403

    # can not create any type of users.
    system_librarian = deepcopy(record)
    librarian = deepcopy(record)
    patron = deepcopy(record)
    counter = 1
    for record in [
        {'data': patron, 'role': 'patron'},
        {'data': librarian, 'role': 'librarian'},
        {'data': system_librarian, 'role': 'system_librarian'}
    ]:
        counter += 1
        data = record['data']
        data['roles'] = [record['role']]
        data['patron']['barcode'] = 'barcode' + str(counter)
        data['email'] = str(counter) + '@domain.com'
        res, _ = postdata(
            client,
            'invenio_records_rest.ptrn_list',
            data
        )
        assert res.status_code == 403
