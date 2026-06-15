# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

from unittest import mock

from flask import current_app
from flask_principal import AnonymousIdentity, identity_changed
from flask_security import login_user

from rero_ils.modules.migrations.permissions import MigrationPermissionPolicy
from rero_ils.modules.patrons.api import Patron, PatronsSearch
from tests.utils import check_permission


@mock.patch.object(Patron, "_extensions", [])
def test_migration_permissions(
    patron_martigny,
    librarian_martigny,
    librarian_sion,
    migration,
):
    """Test library permissions class."""

    # Anonymous user
    identity_changed.send(current_app._get_current_object(), identity=AnonymousIdentity())
    check_permission(
        MigrationPermissionPolicy,
        {
            "search": False,
            "read": False,
            "create": False,
            "update": False,
            "delete": False,
        },
        {},
    )

    # Patron
    #    A simple patron can't operate any operation about Migration
    login_user(patron_martigny.user)
    check_permission(
        MigrationPermissionPolicy,
        {
            "search": False,
            "read": False,
            "create": False,
            "update": False,
            "delete": False,
        },
        migration,
    )

    # Librarian without allowed roles
    librarian_martigny["roles"].remove("pro_library_administrator")
    librarian_martigny["roles"].remove("pro_catalog_manager")
    librarian_martigny.update(librarian_martigny, dbcommit=True, reindex=True)
    PatronsSearch.flush_and_refresh()

    login_user(librarian_martigny.user)
    check_permission(
        MigrationPermissionPolicy,
        {
            "search": False,
            "read": False,
            "create": False,
            "update": False,
            "delete": False,
        },
        migration,
    )

    # Librarian with one allowed roles
    librarian_martigny["roles"].append("pro_library_administrator")
    librarian_martigny.update(librarian_martigny, dbcommit=True, reindex=True)
    PatronsSearch.flush_and_refresh()

    login_user(librarian_martigny.user)
    check_permission(
        MigrationPermissionPolicy,
        {
            "search": True,
            "read": True,
            "create": False,
            "update": True,
            "delete": False,
        },
        migration,
    )

    # Librarian with one allowed roles
    librarian_martigny["roles"].append("pro_catalog_manager")
    librarian_martigny["roles"].remove("pro_library_administrator")
    librarian_martigny.update(librarian_martigny, dbcommit=True, reindex=True)
    PatronsSearch.flush_and_refresh()

    login_user(librarian_martigny.user)
    check_permission(
        MigrationPermissionPolicy,
        {
            "search": True,
            "read": True,
            "create": False,
            "update": True,
            "delete": False,
        },
        migration,
    )

    # Librarian with one allowed roles
    librarian_martigny["roles"].append("pro_full_permissions")
    librarian_martigny["roles"].remove("pro_catalog_manager")
    librarian_martigny.update(librarian_martigny, dbcommit=True, reindex=True)
    PatronsSearch.flush_and_refresh()

    login_user(librarian_martigny.user)
    check_permission(
        MigrationPermissionPolicy,
        {
            "search": True,
            "read": True,
            "create": False,
            "update": True,
            "delete": False,
        },
        migration,
    )

    # reset data for the next tests
    librarian_martigny["roles"].remove("pro_full_permissions")
    librarian_martigny["roles"].append("pro_catalog_manager")
    librarian_martigny.update(librarian_martigny, dbcommit=True, reindex=True)
    PatronsSearch.flush_and_refresh()

    # other organisation
    login_user(librarian_sion.user)
    check_permission(
        MigrationPermissionPolicy,
        {
            "search": True,
            "read": False,
            "create": False,
            "update": False,
            "delete": False,
        },
        migration,
    )
