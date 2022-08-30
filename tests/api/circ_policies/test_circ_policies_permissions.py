# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2020 RERO
# Copyright (C) 2020 UCLouvain
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

from rero_ils.modules.circ_policies.permissions import \
    CirculationPolicyPermissionPolicy as CiPoPermissionPolicy


def test_circ_policies_permissions_api(client, librarian_martigny,
                                       system_librarian_martigny,
                                       circ_policy_short_martigny,
                                       circ_policy_default_sion):
    """Test circulation policies permissions api."""
    cipo_permissions_url = url_for(
        'api_blueprint.permissions',
        route_name='circ_policies'
    )
    cipo_martigny_permissions_url = url_for(
        'api_blueprint.permissions',
        route_name='circ_policies',
        record_pid=circ_policy_short_martigny.pid
    )
    cipo_sion_permissions_url = url_for(
        'api_blueprint.permissions',
        route_name='circ_policies',
        record_pid=circ_policy_default_sion.pid
    )

    # Not logged
    res = client.get(cipo_permissions_url)
    assert res.status_code == 401

    # Logged as librarian
    #   * lib can 'list' cipo
    #   * lib can 'read' cipo from its own organisation
    #   * lib can't never 'create', 'delete', cipo
    #   * lib can update cipo depending of cipo settings
    login_user_via_session(client, librarian_martigny.user)
    res = client.get(cipo_martigny_permissions_url)
    assert res.status_code == 200
    data = get_json(res)
    for action in ['list', 'read']:
        assert data[action]['can']
    for action in ['create', 'update', 'delete']:
        assert not data[action]['can']
    res = client.get(cipo_sion_permissions_url)
    data = get_json(res)
    assert not data['read']['can']

    # Logged as system librarian
    #   * sys_lib can do anything about patron type for its own organisation
    #   * sys_lib can't doo anything about patron type for other organisation
    login_user_via_session(client, system_librarian_martigny.user)
    res = client.get(cipo_martigny_permissions_url)
    assert res.status_code == 200
    data = get_json(res)
    for action in ['list', 'read', 'create', 'update', 'delete']:
        assert data[action]['can']
    res = client.get(cipo_sion_permissions_url)
    assert res.status_code == 200
    data = get_json(res)
    for action in ['update', 'delete']:
        assert not data[action]['can']


def test_circ_policies_permissions(patron_martigny,
                                   librarian_martigny,
                                   system_librarian_martigny,
                                   circ_policy_short_martigny,
                                   circ_policy_default_sion):
    """Test circulation policies permission class."""
    # Anonymous user
    #    An anonymous user can't operate any operation about circulation
    #    policies
    identity_changed.send(
        current_app._get_current_object(), identity=AnonymousIdentity()
    )
    check_permission(CiPoPermissionPolicy, {'search': False}, None)
    check_permission(CiPoPermissionPolicy, {'create': False}, {})
    check_permission(CiPoPermissionPolicy, {
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, circ_policy_short_martigny)

    # Patron
    #    A simple patron can't operate any operation about circulation policies
    login_user(patron_martigny.user)
    check_permission(CiPoPermissionPolicy, {'search': False}, None)
    check_permission(CiPoPermissionPolicy, {'create': False}, {})
    check_permission(CiPoPermissionPolicy, {
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, circ_policy_short_martigny)

    # Librarian
    #     - search : any circulation policies despite organisation owner
    #     - read : only circulation policies for its own organisation
    #     - create/update/delete: disallowed
    login_user(librarian_martigny.user)
    check_permission(CiPoPermissionPolicy, {'search': True}, None)
    check_permission(CiPoPermissionPolicy, {'create': False}, {})
    check_permission(CiPoPermissionPolicy, {
        'read': True,
        'create': False,
        'update': False,
        'delete': False
    }, circ_policy_short_martigny)
    check_permission(CiPoPermissionPolicy, {
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, circ_policy_default_sion)

    # SystemLibrarian
    #     - search : any circulation policies despite organisation owner
    #     - read/create/update/delete : only circulation policies for its own
    #       organisation
    login_user(system_librarian_martigny.user)
    check_permission(CiPoPermissionPolicy, {'search': True}, None)
    check_permission(CiPoPermissionPolicy, {'create': True}, {})
    check_permission(CiPoPermissionPolicy, {
        'read': True,
        'create': True,
        'update': True,
        'delete': True
    }, circ_policy_short_martigny)
    check_permission(CiPoPermissionPolicy, {
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, circ_policy_default_sion)
