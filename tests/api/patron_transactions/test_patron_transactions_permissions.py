# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

from unittest import mock

from flask import current_app
from flask_principal import AnonymousIdentity, identity_changed
from flask_security import login_user

from rero_ils.modules.patron_transactions.permissions import (
    PatronTransactionPermissionPolicy,
)
from rero_ils.modules.patrons.api import Patron, PatronsSearch
from tests.utils import check_permission


@mock.patch.object(Patron, "_extensions", [])
def test_pttr_permissions(
    patron_martigny,
    librarian_martigny,
    system_librarian_martigny,
    patron_transaction_overdue_saxon,
    patron_transaction_overdue_sion,
    patron_transaction_overdue_martigny,
):
    """Test patron transaction permissions class."""

    pttr_martigny = patron_transaction_overdue_martigny
    pttr_saxon = patron_transaction_overdue_saxon
    pttr_sion = patron_transaction_overdue_sion

    # Anonymous user :: all operation disallowed
    identity_changed.send(current_app._get_current_object(), identity=AnonymousIdentity())
    check_permission(
        PatronTransactionPermissionPolicy,
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
        PatronTransactionPermissionPolicy,
        {
            "search": False,
            "read": False,
            "create": False,
            "update": False,
            "delete": False,
        },
        pttr_martigny,
    )

    # Patron user :: could search any, could read own pttr
    login_user(patron_martigny.user)
    check_permission(PatronTransactionPermissionPolicy, {"create": False}, {})
    check_permission(
        PatronTransactionPermissionPolicy,
        {
            "search": True,
            "read": True,
            "create": False,
            "update": False,
            "delete": False,
        },
        pttr_martigny,
    )
    check_permission(
        PatronTransactionPermissionPolicy,
        {
            "read": False,
        },
        pttr_sion,
    )

    # Librarian with specific role
    #     - search: any pttr
    #     - other operations : allowed for pttr of its own organisation
    login_user(librarian_martigny.user)
    check_permission(
        PatronTransactionPermissionPolicy,
        {"search": True, "read": True, "create": True, "update": True, "delete": True},
        pttr_martigny,
    )
    check_permission(
        PatronTransactionPermissionPolicy,
        {"search": True, "read": True, "create": True, "update": True, "delete": True},
        pttr_saxon,
    )
    check_permission(
        PatronTransactionPermissionPolicy,
        {
            "search": True,
            "read": False,
            "create": False,
            "update": False,
            "delete": False,
        },
        pttr_sion,
    )

    # Librarian without specific role
    #   - search: any items
    #   - read: only record of own organisation
    #   - all other operations are disallowed
    original_roles = librarian_martigny.get("roles", [])
    librarian_martigny["roles"] = ["pro_read_only"]
    librarian_martigny.update(librarian_martigny, dbcommit=True, reindex=True)
    PatronsSearch.flush_and_refresh()

    login_user(librarian_martigny.user)  # to refresh identity !
    check_permission(
        PatronTransactionPermissionPolicy,
        {
            "search": True,
            "read": True,
            "create": False,
            "update": False,
            "delete": False,
        },
        pttr_saxon,
    )
    check_permission(
        PatronTransactionPermissionPolicy,
        {
            "search": True,
            "read": False,
            "create": False,
            "update": False,
            "delete": False,
        },
        pttr_sion,
    )

    # reset the librarian
    librarian_martigny["roles"] = original_roles
    librarian_martigny.update(librarian_martigny, dbcommit=True, reindex=True)
    PatronsSearch.flush_and_refresh()
