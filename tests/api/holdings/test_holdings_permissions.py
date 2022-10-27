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

import mock
from flask import current_app
from flask_principal import AnonymousIdentity, identity_changed
from flask_security import login_user
from utils import check_permission, flush_index

from rero_ils.modules.holdings.permissions import HoldingsPermissionPolicy
from rero_ils.modules.patrons.api import Patron, PatronsSearch


@mock.patch.object(Patron, '_extensions', [])
def test_holdings_permissions(
    patron_martigny, org_martigny, librarian_martigny,
    system_librarian_martigny, holding_lib_sion, holding_lib_saxon,
    holding_lib_martigny, holding_lib_martigny_w_patterns,
    holding_lib_saxon_w_patterns, holding_lib_sion_w_patterns
):
    """Test holdings permissions class."""

    # Anonymous user & Patron user
    #  - search/read any document are allowed.
    #  - create/update/delete operations are disallowed.
    identity_changed.send(
        current_app._get_current_object(), identity=AnonymousIdentity()
    )
    check_permission(HoldingsPermissionPolicy, {
        'search': True,
        'read': True,
        'create': False,
        'update': False,
        'delete': False
    }, None)
    check_permission(HoldingsPermissionPolicy, {
        'search': True,
        'read': True,
        'create': False,
        'update': False,
        'delete': False
    }, holding_lib_martigny)
    login_user(patron_martigny.user)
    check_permission(HoldingsPermissionPolicy, {'create': False}, {})
    check_permission(HoldingsPermissionPolicy, {
        'search': True,
        'read': True,
        'create': False,
        'update': False,
        'delete': False
    }, holding_lib_sion)

    # Librarian with specific role
    #     - search/read: any document
    #     - create/update/delete:
    #        -- allowed for serial holdings of its own library
    #        -- disallowed for standard holdings despite its own library
    login_user(librarian_martigny.user)
    check_permission(HoldingsPermissionPolicy, {
        'search': True,
        'read': True,
        'create': False,
        'update': False,
        'delete': False
    }, holding_lib_martigny)
    check_permission(HoldingsPermissionPolicy, {
        'search': True,
        'read': True,
        'create': False,
        'update': False,
        'delete': False
    }, holding_lib_saxon)
    check_permission(HoldingsPermissionPolicy, {
        'search': True,
        'read': True,
        'create': False,
        'update': False,
        'delete': False
    }, holding_lib_sion)
    check_permission(HoldingsPermissionPolicy, {
        'search': True,
        'read': True,
        'create': True,
        'update': True,
        'delete': True
    }, holding_lib_martigny_w_patterns)
    check_permission(HoldingsPermissionPolicy, {
        'search': True,
        'read': True,
        'create': False,
        'update': False,
        'delete': False
    }, holding_lib_saxon_w_patterns)
    check_permission(HoldingsPermissionPolicy, {
        'search': True,
        'read': True,
        'create': False,
        'update': False,
        'delete': False
    }, holding_lib_sion_w_patterns)

    # Librarian without specific role
    #   - search/read: any document
    #   - create/update/delete: disallowed for any holdings !!
    original_roles = librarian_martigny.get('roles', [])
    librarian_martigny['roles'] = ['pro_circulation_manager']
    librarian_martigny.update(librarian_martigny, dbcommit=True, reindex=True)
    flush_index(PatronsSearch.Meta.index)

    login_user(librarian_martigny.user)  # to refresh identity !
    check_permission(HoldingsPermissionPolicy, {
        'search': True,
        'read': True,
        'create': False,
        'update': False,
        'delete': False
    }, holding_lib_martigny_w_patterns)

    # reset the librarian
    librarian_martigny['roles'] = original_roles
    librarian_martigny.update(librarian_martigny, dbcommit=True, reindex=True)
    flush_index(PatronsSearch.Meta.index)

    # System librarian (aka. full-permissions)
    #   - create/update/delete: allow for serial holding if its own org
    login_user(system_librarian_martigny.user)
    check_permission(HoldingsPermissionPolicy, {
        'search': True,
        'read': True,
        'create': True,
        'update': True,
        'delete': True
    }, holding_lib_saxon_w_patterns)
