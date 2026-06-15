# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

from flask import current_app
from flask_principal import AnonymousIdentity, identity_changed
from flask_security import login_user

from rero_ils.modules.stats.permissions import StatisticsPermissionPolicy
from tests.utils import check_permission


def test_stats_permissions(patron_martigny, stats_librarian, librarian_martigny, system_librarian_martigny):
    """Test stat permissions class."""

    # Anonymous user & Patron user :: all operation are disallowed
    identity_changed.send(current_app._get_current_object(), identity=AnonymousIdentity())
    check_permission(
        StatisticsPermissionPolicy,
        {
            "search": False,
            "read": False,
            "create": False,
            "update": False,
            "delete": False,
        },
        None,
    )
    check_permission(
        StatisticsPermissionPolicy,
        {
            "search": False,
            "read": False,
            "create": False,
            "update": False,
            "delete": False,
        },
        stats_librarian,
    )
    login_user(patron_martigny.user)
    check_permission(StatisticsPermissionPolicy, {"create": False}, {})
    check_permission(
        StatisticsPermissionPolicy,
        {
            "search": False,
            "read": False,
            "create": False,
            "update": False,
            "delete": False,
        },
        stats_librarian,
    )

    # Librarian with specific role
    #     - search/read: any items
    #     - create/update/delete: always disallowed
    login_user(librarian_martigny.user)
    check_permission(
        StatisticsPermissionPolicy,
        {
            "search": False,
            "read": False,
            "create": False,
            "update": False,
            "delete": False,
        },
        stats_librarian,
    )

    login_user(system_librarian_martigny.user)
    check_permission(
        StatisticsPermissionPolicy,
        {
            "search": True,
            "read": True,
            "create": False,
            "update": False,
            "delete": False,
        },
        stats_librarian,
    )
