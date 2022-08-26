# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2022 RERO
# Copyright (C) 2022 UCLouvain
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

from flask import current_app, url_for
from flask_principal import AnonymousIdentity, identity_changed
from flask_security.utils import login_user
from invenio_accounts.testutils import login_user_via_session
from utils import check_permission, get_json

from rero_ils.modules.patron_types.permissions import \
    PatronTypePermissionPolicy


def test_item_types_permissions_api(client, librarian_martigny,
                                    system_librarian_martigny,
                                    item_type_standard_martigny,
                                    item_type_regular_sion):
    """Test patron types permissions api."""
    itty_permissions_url = url_for(
        'api_blueprint.permissions',
        route_name='item_types'
    )
    itty_martigny_permissions_url = url_for(
        'api_blueprint.permissions',
        route_name='item_types',
        record_pid=item_type_standard_martigny.pid
    )
    itty_sion_permissions_url = url_for(
        'api_blueprint.permissions',
        route_name='item_types',
        record_pid=item_type_regular_sion.pid
    )

    # Not logged
    res = client.get(itty_permissions_url)
    assert res.status_code == 401

    # Logged as librarian
    #   * lib can 'list' item_type
    #   * lib can 'read' item_type from its own organisation
    #   * lib can't never 'create', 'delete', 'update' item_type
    login_user_via_session(client, librarian_martigny.user)
    res = client.get(itty_martigny_permissions_url)
    assert res.status_code == 200
    data = get_json(res)
    for action in ['list', 'read']:
        assert data[action]['can']
    for action in ['create', 'update', 'delete']:
        assert not data[action]['can']
    res = client.get(itty_sion_permissions_url)
    data = get_json(res)
    assert not data['read']['can']

    # Logged as system librarian
    #   * sys_lib can do anything about item_type for its own organisation
    #   * sys_lib can't do anything about item_type for other organisation
    login_user_via_session(client, system_librarian_martigny.user)
    res = client.get(itty_martigny_permissions_url)
    assert res.status_code == 200
    data = get_json(res)
    for action in ['list', 'read', 'create', 'update', 'delete']:
        assert data[action]['can']
    res = client.get(itty_sion_permissions_url)
    assert res.status_code == 200
    data = get_json(res)
    for action in ['update', 'delete']:
        assert not data[action]['can']


def test_item_types_permissions(patron_martigny,
                                librarian_martigny,
                                system_librarian_martigny,
                                item_type_standard_martigny,
                                item_type_regular_sion):
    """Test patron types permissions class."""
    permission_policy = PatronTypePermissionPolicy

    # Anonymous user
    #    An anonymous user can't operate any operation about item type
    identity_changed.send(
        current_app._get_current_object(), identity=AnonymousIdentity()
    )
    check_permission(permission_policy, {'search': False}, None)
    check_permission(permission_policy, {'create': False}, {})
    check_permission(permission_policy, {
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, item_type_standard_martigny)

    # Patron
    #    A simple patron can't operate any operation about item type
    login_user(patron_martigny.user)
    check_permission(permission_policy, {'search': False}, None)
    check_permission(permission_policy, {'create': False}, {})
    check_permission(permission_policy, {
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, item_type_standard_martigny)

    # Librarian
    #     - search : any item type despite organisation owner
    #     - read : only item type for its own organisation
    #     - create/update/delete: disallowed
    login_user(librarian_martigny.user)
    check_permission(permission_policy, {'search': True}, None)
    check_permission(permission_policy, {'create': False}, {})
    check_permission(permission_policy, {
        'read': True,
        'create': False,
        'update': False,
        'delete': False
    }, item_type_standard_martigny)
    check_permission(permission_policy, {
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, item_type_regular_sion)

    # SystemLibrarian
    #     - search : any item type despite organisation owner
    #     - read/create/update/delete : only item type for its own
    #       organisation
    login_user(system_librarian_martigny.user)
    check_permission(permission_policy, {'search': True}, None)
    check_permission(permission_policy, {'create': True}, {})
    check_permission(permission_policy, {
        'read': True,
        'create': True,
        'update': True,
        'delete': True
    }, item_type_standard_martigny)
    check_permission(permission_policy, {
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, item_type_regular_sion)
