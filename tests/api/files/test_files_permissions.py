# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2024 RERO
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

import mock
from flask import current_app, url_for
from flask_principal import AnonymousIdentity, identity_changed
from flask_security import login_user
from invenio_accounts.testutils import login_user_via_session
from utils import check_permission, flush_index, get_json

from rero_ils.modules.files.permissions import FilePermissionPolicy
from rero_ils.modules.patrons.api import Patron, PatronsSearch


def test_files_permissions_api(client, librarian_martigny,
                               librarian_sion, patron_martigny,
                               system_librarian_martigny,
                               document_with_files):
    """Test files permissions api."""
    record_file = next(document_with_files.get_records_files())
    permissions_list_url = url_for(
        'api_blueprint.permissions',
        route_name='records'
    )
    permissions_item_url = url_for(
        'api_blueprint.permissions',
        route_name='records',
        record_pid=record_file.pid.pid_value
    )

    # Not logged
    res = client.get(permissions_list_url)
    assert res.status_code == 401

    res = client.get(permissions_item_url)
    assert res.status_code == 401

    # logged as patron
    login_user_via_session(client, patron_martigny.user)
    res = client.get(permissions_item_url)
    assert res.status_code == 403

    res = client.get(permissions_list_url)
    assert res.status_code == 403

    # logged as librarian
    login_user_via_session(client, librarian_martigny.user)
    res = client.get(permissions_item_url)
    assert res.status_code == 200
    data = get_json(res)
    for action in ['list', 'read', 'create', 'update', 'delete']:
        assert data[action]['can']

    res = client.get(permissions_list_url)
    assert res.status_code == 200
    data = get_json(res)
    for action in ['list', 'create']:
        assert data[action]['can']

    # logged as librarian
    login_user_via_session(client, system_librarian_martigny.user)
    res = client.get(permissions_item_url)
    assert res.status_code == 200
    data = get_json(res)
    for action in ['list', 'read', 'create', 'update', 'delete']:
        assert data[action]['can']

    res = client.get(permissions_list_url)
    assert res.status_code == 200
    data = get_json(res)
    for action in ['list', 'create']:
        assert data[action]['can']

    # logged as librarian
    login_user_via_session(client, librarian_sion.user)
    res = client.get(permissions_item_url)
    assert res.status_code == 200
    data = get_json(res)
    for action in ['list', 'create', 'read']:
        assert data[action]['can']
    for action in ['update', 'delete']:
        assert not data[action]['can']

    res = client.get(permissions_list_url)
    assert res.status_code == 200
    data = get_json(res)
    for action in ['list', 'create']:
        assert data[action]['can']


@mock.patch.object(Patron, '_extensions', [])
def test_files_permissions(
    patron_martigny, librarian_martigny, librarian_sion,
    system_librarian_martigny, document_with_files
):
    """Test files permissions."""

    # Anonymous user & Patron user
    #  - search/read any files are allowed.
    #  - create/update/delete operations are disallowed.
    identity_changed.send(
        current_app._get_current_object(), identity=AnonymousIdentity()
    )
    check_permission(FilePermissionPolicy, {
        'search': True,
        'read': True,
        'create': False,
        'update': False,
        'delete': False
    }, None)
    record_file = next(document_with_files.get_records_files())
    check_permission(FilePermissionPolicy, {
        'search': True,
        'read': True,
        'create': False,
        'update': False,
        'delete': False
    }, record_file)
    login_user(patron_martigny.user)
    check_permission(FilePermissionPolicy, {'create': False}, {})
    check_permission(FilePermissionPolicy, {
        'search': True,
        'read': True,
        'create': False,
        'update': False,
        'delete': False
    }, record_file)

    # Librarian with specific role
    #     - search/read: any files
    #     - create/update/delete: allowed for files of its own library
    login_user(librarian_martigny.user)
    check_permission(FilePermissionPolicy, {
        'search': True,
        'read': True,
        'create': True,
        'update': True,
        'delete': True
    }, record_file)

    # Librarian with specific role
    #     - search/read: any files
    #     - update/delete: disallowed for files of other libraries
    login_user(librarian_sion.user)
    check_permission(FilePermissionPolicy, {
        'search': True,
        'read': True,
        'create': True,
        'update': False,
        'delete': False
    }, record_file)

    # Librarian without specific role
    #   - search/read: any files
    #   - create/update/delete: allowed for any files of its own library
    original_roles = librarian_martigny.get('roles', [])
    librarian_martigny['roles'] = ['pro_catalog_manager']
    librarian_martigny.update(librarian_martigny, dbcommit=True, reindex=True)
    flush_index(PatronsSearch.Meta.index)

    login_user(librarian_martigny.user)  # to refresh identity !
    check_permission(FilePermissionPolicy, {
        'search': True,
        'read': True,
        'create': True,
        'update': True,
        'delete': True
    }, record_file)

    librarian_martigny['roles'] = ['pro_user_manager']
    librarian_martigny.update(librarian_martigny, dbcommit=True, reindex=True)
    flush_index(PatronsSearch.Meta.index)

    login_user(librarian_martigny.user)  # to refresh identity !
    check_permission(FilePermissionPolicy, {
        'search': True,
        'read': True,
        'create': False,
        'update': False,
        'delete': False
    }, record_file)

    # reset the librarian
    librarian_martigny['roles'] = original_roles
    librarian_martigny.update(librarian_martigny, dbcommit=True, reindex=True)
    flush_index(PatronsSearch.Meta.index)

    # System librarian (aka. full-permissions)
    #   - create/update/delete: allow for files if its own org
    login_user(system_librarian_martigny.user)
    check_permission(FilePermissionPolicy, {
        'search': True,
        'read': True,
        'create': True,
        'update': True,
        'delete': True
    }, record_file)
