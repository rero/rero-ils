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

from rero_ils.modules.stats.permissions import StatisticsPermissionPolicy


def test_stats_permissions(
    patron_martigny, stats_librarian, librarian_martigny,
    system_librarian_martigny
):
    """Test stat permissions class."""

    # Anonymous user & Patron user :: all operation are disallowed
    identity_changed.send(
        current_app._get_current_object(), identity=AnonymousIdentity()
    )
    check_permission(StatisticsPermissionPolicy, {
        'search': False,
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, None)
    check_permission(StatisticsPermissionPolicy, {
        'search': False,
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, stats_librarian)
    login_user(patron_martigny.user)
    check_permission(StatisticsPermissionPolicy, {'create': False}, {})
    check_permission(StatisticsPermissionPolicy, {
        'search': False,
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, stats_librarian)

    # Librarian with specific role
    #     - search/read: any items
    #     - create/update/delete: always disallowed
    login_user(librarian_martigny.user)
    check_permission(StatisticsPermissionPolicy, {
        'search': False,
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, stats_librarian)

    login_user(system_librarian_martigny.user)
    check_permission(StatisticsPermissionPolicy, {
        'search': True,
        'read': True,
        'create': False,
        'update': False,
        'delete': False
    }, stats_librarian)
