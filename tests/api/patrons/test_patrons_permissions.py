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

import mock
from flask import current_app
from flask_principal import AnonymousIdentity, identity_changed
from flask_security import login_user
from utils import check_permission, flush_index

from rero_ils.modules.patrons.api import Patron, PatronsSearch
from rero_ils.modules.patrons.permissions import PatronPermissionPolicy
from rero_ils.modules.users.models import UserRole


@mock.patch.object(Patron, '_extensions', [])
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
        'delete': False  # simple librarian cannot delete other librarian
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

    # reset librarian
    # reset the librarian
    librarian_martigny['roles'] = original_roles
    librarian_martigny.update(librarian_martigny, dbcommit=True, reindex=True)
    flush_index(PatronsSearch.Meta.index)

    original_roles = patron_martigny.get('roles', [])

    # librarian + patron roles
    patron_martigny['roles'] = [UserRole.FULL_PERMISSIONS, UserRole.PATRON]
    patron_martigny['libraries'] = librarian_martigny['libraries']
    patron_martigny.update(patron_martigny, dbcommit=True, reindex=True)
    flush_index(PatronsSearch.Meta.index)

    login_user(patron_martigny.user)  # to refresh identity !
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

    patron_martigny['roles'] = original_roles
    del patron_martigny['libraries']
    patron_martigny.update(patron_martigny, dbcommit=True, reindex=True)
    flush_index(PatronsSearch.Meta.index)
