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

import mock
from flask import current_app
from flask_principal import AnonymousIdentity, identity_changed
from flask_security import login_user
from utils import check_permission, flush_index

from rero_ils.modules.libraries.permissions import LibraryPermissionPolicy
from rero_ils.modules.patrons.api import Patron, PatronsSearch


@mock.patch.object(Patron, '_extensions', [])
def test_library_permissions(patron_martigny,
                             librarian_martigny,
                             system_librarian_martigny,
                             org_martigny, lib_martigny, lib_saxon, lib_sion):
    """Test library permissions class."""

    # Anonymous user
    identity_changed.send(
        current_app._get_current_object(), identity=AnonymousIdentity()
    )
    check_permission(LibraryPermissionPolicy, {
        'search': False,
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, {})

    # Patron
    #    A simple patron can't operate any operation about Library
    login_user(patron_martigny.user)
    check_permission(LibraryPermissionPolicy, {
        'search': False,
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, lib_martigny)

    # Librarian without 'pro_library_administrator' role
    #     - search : any Library despite organisation owner
    #     - read : only Library for its own organisation
    #     - create/update/delete : disallowed
    librarian_martigny['roles'].remove('pro_library_administrator')
    librarian_martigny.update(librarian_martigny, dbcommit=True, reindex=True)
    flush_index(PatronsSearch.Meta.index)

    login_user(librarian_martigny.user)
    check_permission(LibraryPermissionPolicy, {'search': True}, None)
    check_permission(LibraryPermissionPolicy, {'create': False}, {})
    check_permission(LibraryPermissionPolicy, {
        'read': True,
        'create': False,
        'update': False,
        'delete': False
    }, lib_martigny)
    check_permission(LibraryPermissionPolicy, {
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, lib_sion)

    # reset the librarian.
    librarian_martigny['roles'].append('pro_library_administrator')
    librarian_martigny.update(librarian_martigny, dbcommit=True, reindex=True)
    flush_index(PatronsSearch.Meta.index)

    # Librarian with 'pro_library_administrator' role
    #    - search/read : same as common librarian
    #    - create/update/delete : if patron is manager for this library

    login_user(librarian_martigny.user)
    check_permission(LibraryPermissionPolicy, {
        'read': True,
        'create': True,
        'update': True,
        'delete': True
    }, lib_martigny)
    check_permission(LibraryPermissionPolicy, {
        'read': True,
        'create': False,
        'update': False,
        'delete': False
    }, lib_saxon)
    check_permission(LibraryPermissionPolicy, {
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, lib_sion)

    # SystemLibrarian
    #     - search : any Library despite organisation owner
    #     - read : only Library for its own organisation
    #     - create/update/delete : only Library for its own organisation
    login_user(system_librarian_martigny.user)
    check_permission(LibraryPermissionPolicy, {
        'read': True,
        'create': True,
        'update': True,
        'delete': True
    }, lib_martigny)
    check_permission(LibraryPermissionPolicy, {
        'read': True,
        'create': True,
        'update': True,
        'delete': True
    }, lib_saxon)
    check_permission(LibraryPermissionPolicy, {
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, lib_sion)
