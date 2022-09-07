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

from flask import current_app
from flask_principal import AnonymousIdentity, identity_changed
from flask_security import login_user
from utils import check_permission

from rero_ils.modules.locations.permissions import LocationPermissionPolicy


def test_location_permissions(patron_martigny,
                              librarian_martigny,
                              librarian2_martigny,
                              system_librarian_martigny,
                              org_martigny, loc_public_martigny,
                              loc_public_saxon, loc_public_sion):
    """Test location permissions class."""

    # Anonymous user
    identity_changed.send(
        current_app._get_current_object(), identity=AnonymousIdentity()
    )
    check_permission(LocationPermissionPolicy, {
        'search': False,
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, {})

    # Patron
    #    A simple patron can't operate any operation about Location
    login_user(patron_martigny.user)
    check_permission(LocationPermissionPolicy, {
        'search': False,
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, loc_public_martigny)

    # Librarian without 'pro_library_administrator' role
    #     - search : any Library despite organisation owner
    #     - read : only Library for its own organisation
    #     - create/update/delete : disallowed
    login_user(librarian2_martigny.user)
    check_permission(LocationPermissionPolicy, {'search': True}, None)
    check_permission(LocationPermissionPolicy, {'create': False}, {})
    check_permission(LocationPermissionPolicy, {
        'read': True,
        'create': False,
        'update': False,
        'delete': False
    }, loc_public_martigny)
    check_permission(LocationPermissionPolicy, {
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, loc_public_sion)

    # Librarian with 'pro_library_administrator' role
    #    - search/read : same as common librarian
    #    - create/update/delete : if patron is manager for this library

    login_user(librarian_martigny.user)
    check_permission(LocationPermissionPolicy, {
        'read': True,
        'create': True,
        'update': True,
        'delete': True
    }, loc_public_martigny)
    check_permission(LocationPermissionPolicy, {
        'read': True,
        'create': False,
        'update': False,
        'delete': False
    }, loc_public_saxon)
    check_permission(LocationPermissionPolicy, {
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, loc_public_sion)

    # SystemLibrarian
    #     - search : any Library despite organisation owner
    #     - read : only Library for its own organisation
    #     - create/update/delete : only Library for its own organisation
    login_user(system_librarian_martigny.user)
    check_permission(LocationPermissionPolicy, {
        'read': True,
        'create': True,
        'update': True,
        'delete': True
    }, loc_public_martigny)
    check_permission(LocationPermissionPolicy, {
        'read': True,
        'create': True,
        'update': True,
        'delete': True
    }, loc_public_saxon)
    check_permission(LocationPermissionPolicy, {
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, loc_public_sion)
