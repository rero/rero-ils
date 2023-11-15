# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
# Copyright (C) 2019-2023 UCLouvain
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

"""Tests Marshmallow schema through REST API for Patrons."""
import json

from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import postdata

from rero_ils.modules.patrons.api import Patron
from rero_ils.modules.patrons.utils import create_user_from_data
from rero_ils.modules.users.models import UserRole


def test_patrons_marshmallow_loaders(
    client, librarian_martigny, system_librarian_martigny_data_tmp,
    json_header
):
    """Test marshmallow schema/restrictions for Patron resources."""

    # TEST#1 :: Use console to manage patron/role
    #   Using 'console' commands, no matter connected user, all operations are
    #   allowed on a Patron, even changes any roles.
    user_data = create_user_from_data(system_librarian_martigny_data_tmp)
    from rero_ils.modules.users.api import User
    user_data = User.remove_fields(user_data)
    patron = Patron.create(user_data, dbcommit=True, reindex=True)
    assert patron and patron['roles'] == [UserRole.FULL_PERMISSIONS]

    roles = [UserRole.ACQUISITION_MANAGER, UserRole.CATALOG_MANAGER]
    patron['roles'] = roles
    patron = patron.update(patron, dbcommit=True, reindex=True)
    patron = Patron.get_record_by_pid(patron.pid)
    assert patron['roles'] == roles

    patron.delete(dbcommit=True, delindex=True)
    patron = Patron.get_record_by_pid(patron.pid)
    assert not patron

    # TEST#2 :: Use API to create patron.
    #   Through the API, the `role` field is controlled by marshmallow
    #   validation process. A simple staff member isn't allowed to control all
    #   roles.
    login_user_via_session(client, librarian_martigny.user)

    user_data['roles'] = [UserRole.FULL_PERMISSIONS]
    user_data = create_user_from_data(system_librarian_martigny_data_tmp)
    del (user_data['pid'])

    # Step 1 :: Send POST API to create user with bad roles --> 400
    #   Should fail because the current logged user doesn't have authorization
    #   to deal with `roles` of the user data.
    res, response_data = postdata(
        client, 'invenio_records_rest.ptrn_list', user_data)
    assert res.status_code == 400
    assert 'Validation error' in response_data['message']

    # Step 2 :: Send POST API to create user with correct roles --> 201
    #   Update user data with correct `roles` values and create the
    #   user.
    original_roles = librarian_martigny['roles']
    librarian_martigny['roles'] = [UserRole.LIBRARY_ADMINISTRATOR]
    librarian_martigny.update(librarian_martigny, dbcommit=True, reindex=True)
    login_user_via_session(client, librarian_martigny.user)

    user_data['roles'] = [UserRole.USER_MANAGER]
    res, response_data = postdata(
        client, 'invenio_records_rest.ptrn_list', user_data)
    assert res.status_code == 201
    pid = response_data['metadata']['pid']

    # Step 3 :: Send PUT API to update roles --> 400
    #   Try to update the created patron to add it some unauthorized roles
    item_url = url_for('invenio_records_rest.ptrn_item', pid_value=pid)
    user_data['pid'] = pid
    user_data['roles'] = [UserRole.FULL_PERMISSIONS]
    res = client.put(item_url, data=json.dumps(user_data), headers=json_header)
    assert res.status_code == 400
    assert 'Validation error' in res.json['message']

    # Step 4 :: Update the patron using console
    #   Force the patron update using console
    patron = Patron.get_record_by_pid(pid)
    patron['roles'] = [UserRole.FULL_PERMISSIONS]
    patron.update(patron, dbcommit=True, reindex=True)
    patron = Patron.get_record_by_pid(pid)
    assert patron['roles'] == [UserRole.FULL_PERMISSIONS]

    # Step 5 :: Delete patron through API
    #   This should be disallowed due to role management restrictions.
    res = client.delete(item_url)
    assert res.status_code == 403

    # Reset the fixtures
    patron.delete(True, True, True)
    librarian_martigny['roles'] = original_roles
    librarian_martigny.update(librarian_martigny, dbcommit=True, reindex=True)
