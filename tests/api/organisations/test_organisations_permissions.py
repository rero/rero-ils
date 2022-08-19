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
from flask_security import login_user
from invenio_accounts.testutils import login_user_via_session
from utils import check_permission, get_json

from rero_ils.modules.organisations.permissions import \
    OrganisationPermissionPolicy


def test_organisation_permissions_api(client, patron_martigny,
                                      org_martigny, org_sion,
                                      system_librarian_martigny):
    """Test organisations permissions api."""
    org_permissions_url = url_for(
        'api_blueprint.permissions',
        route_name='organisations'
    )
    org_martigny_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='organisations',
        record_pid=org_martigny.pid
    )
    org_sion_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='organisations',
        record_pid=org_sion.pid
    )

    # Not logged
    res = client.get(org_permissions_url)
    assert res.status_code == 401

    # Logged as patron
    login_user_via_session(client, patron_martigny.user)
    res = client.get(org_permissions_url)
    assert res.status_code == 403

    # Logged as system librarian
    #   * sys_lib can 'list' organisations
    #   * sys_lib can never 'create' and 'delete' any organisation
    #   * sys_lib can 'read' and 'update' only their own organisation
    login_user_via_session(client, system_librarian_martigny.user)
    res = client.get(org_martigny_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert not data['create']['can']
    assert data['update']['can']
    assert not data['delete']['can']

    res = client.get(org_sion_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert not data['read']['can']
    assert not data['update']['can']


def test_organisation_permissions(patron_martigny,
                                  librarian_martigny,
                                  system_librarian_martigny,
                                  org_martigny, org_sion):
    """Test organisation permissions class."""

    permission_policy = OrganisationPermissionPolicy

    # Anonymous user
    identity_changed.send(
        current_app._get_current_object(), identity=AnonymousIdentity()
    )
    check_permission(permission_policy, {
        'search': False,
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, {})

    # Patron
    #    A simple patron can't operate any operation about Organisation
    login_user(patron_martigny.user)
    check_permission(permission_policy, {
        'search': False,
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, org_martigny)

    # Librarian
    #     - search : any Organisation despite organisation owner
    #     - read : only Organisation for its own organisation
    #     - create/update/delete: disallowed
    login_user(librarian_martigny.user)
    check_permission(permission_policy, {'search': True}, None)
    check_permission(permission_policy, {'create': False}, {})
    check_permission(permission_policy, {
        'read': True,
        'create': False,
        'update': False,
        'delete': False
    }, org_martigny)
    check_permission(permission_policy, {
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, org_sion)

    # SystemLibrarian
    #     - search : any Organisation despite organisation owner
    #     - read/update : only Organisation for its own organisation
    #     - create/delete : always disallowed (only CLI command)
    login_user(system_librarian_martigny.user)
    check_permission(permission_policy, {'search': True}, None)
    check_permission(permission_policy, {'create': False}, {})
    check_permission(permission_policy, {
        'read': True,
        'create': False,
        'update': True,
        'delete': False
    }, org_martigny)
    check_permission(permission_policy, {
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, org_sion)
