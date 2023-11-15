# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2022-2023 RERO
# Copyright (C) 2022-2023 UCLouvain
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

from rero_ils.modules.stats_cfg.permissions import \
    StatisticsConfigurationPermissionPolicy


def test_stats_cfg_permissions(
    patron_martigny, stats_cfg_martigny, stats_cfg_sion,
    librarian_martigny, system_librarian_martigny, librarian_saxon, lib_saxon
):
    """Test statistics configuration permissions class."""

    # Anonymous user & Patron user :: all operation are disallowed
    identity_changed.send(
        current_app._get_current_object(), identity=AnonymousIdentity()
    )
    check_permission(StatisticsConfigurationPermissionPolicy, {
        'search': False,
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, None)
    check_permission(StatisticsConfigurationPermissionPolicy, {
        'search': False,
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, stats_cfg_martigny)
    login_user(patron_martigny.user)
    check_permission(StatisticsConfigurationPermissionPolicy,
                     {'create': False}, {})
    check_permission(StatisticsConfigurationPermissionPolicy, {
        'search': False,
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, stats_cfg_martigny)

    # Librarian with specific role
    #     - search/read: any items
    login_user(librarian_martigny.user)
    check_permission(StatisticsConfigurationPermissionPolicy, {
        'search': False,
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, stats_cfg_martigny)

    # Librarian with the right role
    # cannot update or delete a config of an other lib
    login_user(librarian_saxon.user)
    check_permission(StatisticsConfigurationPermissionPolicy, {
        'search': True,
        'read': True,
        'create': True,
        'update': False,
        'delete': False
    }, stats_cfg_martigny)

    # Librarian with the right role
    # can update or delete a config of this library
    stats_cfg_martigny.update(
        dict(
            library={
                '$ref': f'https://bib.test.rero.ch/libraries/{lib_saxon.pid}'
            }))
    check_permission(StatisticsConfigurationPermissionPolicy, {
        'search': True,
        'read': True,
        'create': True,
        'update': True,
        'delete': True
    }, stats_cfg_martigny)

    # System librarian with specific role
    #     - search/read: any items
    login_user(system_librarian_martigny.user)
    check_permission(StatisticsConfigurationPermissionPolicy, {
        'search': True,
        'read': True,
        'create': True,
        'update': True,
        'delete': True
    }, stats_cfg_martigny)

    check_permission(StatisticsConfigurationPermissionPolicy, {
        'search': True,
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, stats_cfg_sion)
