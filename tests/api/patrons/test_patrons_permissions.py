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

"""Tests Permission for REST API patrons."""

from copy import deepcopy

from flask import current_app
from flask_principal import AnonymousIdentity, identity_changed
from flask_security import login_user
from utils import check_permission, flush_index

from rero_ils.modules.patrons.api import Patron, PatronsSearch
from rero_ils.modules.patrons.permissions import PatronPermissionPolicy
from rero_ils.modules.users.models import UserRole
from rero_ils.modules.utils import get_ref_for_pid


def test_patrons_permissions(
    patron_martigny, librarian_martigny, system_librarian_martigny,
    org_martigny, librarian_saxon, patron_sion, patron2_martigny,
    librarian2_martigny, librarian2_martigny_data, lib_saxon
):
    """Test patrons permissions class."""

    # Anonymous user & Patron user
    identity_changed.send(
        current_app._get_current_object(), identity=AnonymousIdentity()
    )
    check_permission(PatronPermissionPolicy, {'search': False}, {})
    check_permission(PatronPermissionPolicy, {
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, None)
    check_permission(PatronPermissionPolicy, {
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, patron_martigny)
    login_user(patron_martigny.user)
    check_permission(PatronPermissionPolicy, {'search': False}, {})
    check_permission(PatronPermissionPolicy, {'create': False}, {})
    check_permission(PatronPermissionPolicy, {
        'read': True,
        'create': False,
        'update': False,
        'delete': False
    }, patron_martigny)
    check_permission(PatronPermissionPolicy, {
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, patron2_martigny)

    # Librarian without any specific role
    #     - search/read: any patrons of its own organisation
    #     - create/update/delete: disallowed
    original_roles = librarian_martigny.get('roles', [])
    librarian_martigny['roles'] = [UserRole.CIRCULATION_MANAGER]
    librarian_martigny.update(librarian_martigny, dbcommit=True, reindex=True)
    flush_index(PatronsSearch.Meta.index)

    login_user(librarian_martigny.user)  # to refresh identity !
    check_permission(PatronPermissionPolicy, {'search': True}, {})
    check_permission(PatronPermissionPolicy, {
        'read': True,
        'create': False,
        'update': False,
        'delete': False
    }, patron_martigny)
    check_permission(PatronPermissionPolicy, {
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, patron_sion)

    # Librarian with specific 'user-management'
    #   - operation allowed on any 'patron' of its own organisation
    #   - operation allowed on any 'staff_member' of its own manageable
    #     libraries
    #   - can only manage 'patron' roles and 'pro_user_manager' role. Any
    #     operation including roles management outside this scope must be
    #     denied.
    librarian_martigny['roles'] = [UserRole.USER_MANAGER]
    librarian_martigny.update(librarian_martigny, dbcommit=True, reindex=True)
    flush_index(PatronsSearch.Meta.index)

    login_user(librarian_martigny.user)  # to refresh identity !
    check_permission(PatronPermissionPolicy, {'search': True}, {})
    check_permission(PatronPermissionPolicy, {
        'read': True,
        'create': True,
        'update': True,
        'delete': True
    }, patron_martigny)
    check_permission(PatronPermissionPolicy, {
        'read': True,
        'create': True,
        'update': True,
        'delete': True
    }, patron2_martigny)
    check_permission(PatronPermissionPolicy, {
        'read': True,
        'create': True,
        'update': True,
        'delete': True
    }, librarian2_martigny)
    check_permission(PatronPermissionPolicy, {
        'read': True,
        'create': False,
        'update': False,
        'delete': False
    }, librarian_saxon)
    check_permission(PatronPermissionPolicy, {
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, patron_sion)

    # test roles' management ::
    #   As specified into the configuration file, the only roles that a
    #   'pro_user_manager' can update is `patron`, any other changes on roles'
    #   management will be denied.
    patron_data = deepcopy(librarian2_martigny_data)
    patron_data['roles'].append(UserRole.PATRON)
    check_permission(PatronPermissionPolicy, {
        'create': True,
        'update': True,
        'delete': True
    }, Patron(patron_data))
    patron_data['roles'].remove(UserRole.USER_MANAGER)
    check_permission(PatronPermissionPolicy, {
        'create': False,
        'update': False,
        'delete': False
    }, Patron(patron_data))

    # Logges as a 'librarian-administrator'
    #   As library-admin, more roles' management are available. According to
    #   the configuration file, user can manage all roles except 'lib-admin'
    #   and 'full-permissions'.
    librarian_martigny['roles'] = [UserRole.LIBRARY_ADMINISTRATOR]
    librarian_martigny.update(librarian_martigny, dbcommit=True, reindex=True)
    flush_index(PatronsSearch.Meta.index)
    login_user(librarian_martigny.user)

    # Don't change any data from last test, now, it will be passed...
    check_permission(PatronPermissionPolicy, {
        'create': True,
        'update': True,
        'delete': True
    }, Patron(patron_data))
    # ... but I cannot manage 'pro_library_administrator' or 'full_permissions'
    patron_data['roles'].append(UserRole.LIBRARY_ADMINISTRATOR)
    check_permission(PatronPermissionPolicy, {
        'create': False,
        'update': False,
        'delete': False
    }, Patron(patron_data))
    # ... But it will be OK only for user of its own library ...
    patron_data['roles'].remove(UserRole.LIBRARY_ADMINISTRATOR)
    patron_data['libraries'][0]['$ref'] = get_ref_for_pid('lib', lib_saxon.pid)
    check_permission(PatronPermissionPolicy, {
        'create': False,
        'update': False,
        'delete': False
    }, Patron(patron_data))

    # Logges as a 'full-permissions'
    #   As 'full-permission' user, I can manage any roles in any library of my
    #   organisation.
    login_user(system_librarian_martigny.user)
    patron_data['roles'].append(UserRole.FULL_PERMISSIONS)
    check_permission(PatronPermissionPolicy, {
        'create': True,
        'update': True,
        'delete': True
    }, Patron(patron_data))

    # reset librarian
    # reset the librarian
    librarian_martigny['roles'] = original_roles
    librarian_martigny.update(librarian_martigny, dbcommit=True, reindex=True)
    flush_index(PatronsSearch.Meta.index)
