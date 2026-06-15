# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

from unittest import mock

from flask import current_app
from flask_principal import AnonymousIdentity, identity_changed
from flask_security import login_user

from rero_ils.modules.operation_logs.permissions import OperationLogPermissionPolicy
from rero_ils.modules.patrons.api import Patron, PatronsSearch
from tests.utils import check_permission


@mock.patch.object(Patron, "_extensions", [])
def test_operation_logs_permissions(patron_martigny, operation_log, librarian_martigny):
    """Test item permissions class."""

    # Anonymous user & Patron user
    #  - search/read any items are allowed.
    #  - create/update/delete operations are disallowed.
    identity_changed.send(current_app._get_current_object(), identity=AnonymousIdentity())
    check_permission(
        OperationLogPermissionPolicy,
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
        OperationLogPermissionPolicy,
        {
            "search": False,
            "read": False,
            "create": False,
            "update": False,
            "delete": False,
        },
        operation_log,
    )
    login_user(patron_martigny.user)
    check_permission(OperationLogPermissionPolicy, {"create": False}, {})
    check_permission(
        OperationLogPermissionPolicy,
        {
            "search": True,
            "read": False,
            "create": False,
            "update": False,
            "delete": False,
        },
        operation_log,
    )

    # Librarian with specific role
    #     - search/read: any items
    #     - create/update/delete: allowed for items of its own library
    login_user(librarian_martigny.user)
    check_permission(
        OperationLogPermissionPolicy,
        {
            "search": True,
            "read": True,
            "create": False,
            "update": False,
            "delete": False,
        },
        operation_log,
    )

    # Librarian without specific role :: No action allowed
    original_roles = librarian_martigny.get("roles", [])
    librarian_martigny["roles"] = ["pro_user_manager"]
    librarian_martigny.update(librarian_martigny, dbcommit=True, reindex=True)
    PatronsSearch.flush_and_refresh()

    login_user(librarian_martigny.user)  # to refresh identity !
    check_permission(
        OperationLogPermissionPolicy,
        {
            "search": True,
            "read": False,
            "create": False,
            "update": False,
            "delete": False,
        },
        operation_log,
    )

    # reset the librarian
    librarian_martigny["roles"] = original_roles
    librarian_martigny.update(librarian_martigny, dbcommit=True, reindex=True)
    PatronsSearch.flush_and_refresh()
