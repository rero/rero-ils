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

from rero_ils.modules.notifications.permissions import \
    NotificationPermissionPolicy
from rero_ils.modules.patrons.api import Patron, PatronsSearch


@mock.patch.object(Patron, '_extensions', [])
def test_notifcations_permissions(
    patron_martigny, librarian2_martigny, system_librarian_martigny,
    org_martigny, notification_late_sion, notification_late_martigny,
    notification_late_saxon
):
    """Test notifications permissions class."""
    # Anonymous user & Patron user
    #  - search/read any items are allowed.
    #  - create/update/delete operations are disallowed.
    identity_changed.send(
        current_app._get_current_object(), identity=AnonymousIdentity()
    )
    check_permission(NotificationPermissionPolicy, {
        'search': False,
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, None)
    check_permission(NotificationPermissionPolicy, {
        'search': False,
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, notification_late_martigny)
    login_user(patron_martigny.user)
    check_permission(NotificationPermissionPolicy, {'create': False}, {})
    check_permission(NotificationPermissionPolicy, {
        'search': True,
        'read': True,
        'create': False,
        'update': False,
        'delete': False
    }, notification_late_martigny)

    # Librarian without specific role
    #   - search/read: any notifications
    #   - create/update/delete: disallowed for any notifications
    login_user(librarian2_martigny.user)
    check_permission(NotificationPermissionPolicy, {
        'search': True,
        'read': True,
        'create': False,
        'update': False,
        'delete': False
    }, notification_late_martigny)
    check_permission(NotificationPermissionPolicy, {
        'search': True,
        'read': True,
        'create': False,
        'update': False,
        'delete': False
    }, notification_late_saxon)
    check_permission(NotificationPermissionPolicy, {
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, notification_late_sion)

    # Librarian administrator
    original_roles = librarian2_martigny.get('roles', [])
    librarian2_martigny['roles'] = ['pro_library_administrator']
    librarian2_martigny.update(librarian2_martigny,
                               dbcommit=True, reindex=True)
    flush_index(PatronsSearch.Meta.index)

    login_user(librarian2_martigny.user)
    check_permission(NotificationPermissionPolicy, {
        'search': True,
        'read': True,
        'create': True,
        'update': True,
        'delete': True
    }, notification_late_martigny)
    check_permission(NotificationPermissionPolicy, {
        'search': True,
        'read': True,
        'create': False,
        'update': False,
        'delete': False
    }, notification_late_saxon)
    check_permission(NotificationPermissionPolicy, {
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, notification_late_sion)

    # reset the librarian
    librarian2_martigny['roles'] = original_roles
    librarian2_martigny.update(librarian2_martigny,
                               dbcommit=True, reindex=True)
    flush_index(PatronsSearch.Meta.index)

    # System librarian (aka. full-permissions)
    #   - create/update/delete: allow for notification if its own org
    login_user(system_librarian_martigny.user)
    check_permission(NotificationPermissionPolicy, {
        'search': True,
        'read': True,
        'create': True,
        'update': True,
        'delete': True
    }, notification_late_martigny)
    check_permission(NotificationPermissionPolicy, {
        'search': True,
        'read': True,
        'create': True,
        'update': True,
        'delete': True
    }, notification_late_saxon)
    check_permission(NotificationPermissionPolicy, {
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, notification_late_sion)
