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

from rero_ils.modules.patron_transaction_events.permissions import \
    PatronTransactionEventPermissionPolicy
from rero_ils.modules.patrons.api import Patron, PatronsSearch


@mock.patch.object(Patron, '_extensions', [])
def test_ptre_permissions(
    patron_martigny, librarian_martigny, system_librarian_martigny,
    patron_transaction_overdue_event_saxon,
    patron_transaction_overdue_event_sion,
    patron_transaction_overdue_event_martigny
):
    """Test patron transaction event permissions class."""

    ptre_martigny = patron_transaction_overdue_event_martigny
    ptre_saxon = patron_transaction_overdue_event_saxon
    ptre_sion = patron_transaction_overdue_event_sion

    # Anonymous user :: all operation disallowed
    identity_changed.send(
        current_app._get_current_object(), identity=AnonymousIdentity()
    )
    check_permission(PatronTransactionEventPermissionPolicy, {
        'search': False,
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, None)
    check_permission(PatronTransactionEventPermissionPolicy, {
        'search': False,
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, ptre_martigny)

    # Patron user :: could search any, could read own pttr
    login_user(patron_martigny.user)
    check_permission(PatronTransactionEventPermissionPolicy, {
        'create': False
    }, {})
    check_permission(PatronTransactionEventPermissionPolicy, {
        'search': True,
        'read': True,
        'create': False,
        'update': False,
        'delete': False
    }, ptre_martigny)
    check_permission(PatronTransactionEventPermissionPolicy, {
        'read': False,
    }, ptre_sion)

    # Librarian with specific role
    #     - search: any pttr
    #     - other operations : allowed for pttr of its own organisation
    login_user(librarian_martigny.user)
    check_permission(PatronTransactionEventPermissionPolicy, {
        'search': True,
        'read': True,
        'create': True,
        'update': True,
        'delete': True
    }, ptre_martigny)
    check_permission(PatronTransactionEventPermissionPolicy, {
        'search': True,
        'read': True,
        'create': True,
        'update': True,
        'delete': True
    }, ptre_saxon)
    check_permission(PatronTransactionEventPermissionPolicy, {
        'search': True,
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, ptre_sion)

    # Librarian without specific role
    #   - search: any items
    #   - read: only record of own organisation
    #   - all other operations are disallowed
    original_roles = librarian_martigny.get('roles', [])
    librarian_martigny['roles'] = ['pro_read_only']
    librarian_martigny.update(librarian_martigny, dbcommit=True, reindex=True)
    flush_index(PatronsSearch.Meta.index)

    login_user(librarian_martigny.user)  # to refresh identity !
    check_permission(PatronTransactionEventPermissionPolicy, {
        'search': True,
        'read': True,
        'create': False,
        'update': False,
        'delete': False
    }, ptre_saxon)
    check_permission(PatronTransactionEventPermissionPolicy, {
        'search': True,
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, ptre_sion)

    # reset the librarian
    librarian_martigny['roles'] = original_roles
    librarian_martigny.update(librarian_martigny, dbcommit=True, reindex=True)
    flush_index(PatronsSearch.Meta.index)
