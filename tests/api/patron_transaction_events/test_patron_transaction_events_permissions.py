# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

from unittest import mock

from flask import current_app
from flask_principal import AnonymousIdentity, identity_changed
from flask_security import login_user

from rero_ils.modules.patron_transaction_events.permissions import (
    PatronTransactionEventPermissionPolicy,
)
from rero_ils.modules.patrons.api import Patron, PatronsSearch
from tests.utils import check_permission


@mock.patch.object(Patron, "_extensions", [])
def test_ptre_permissions(
    patron_martigny,
    librarian_martigny,
    system_librarian_martigny,
    patron_transaction_overdue_event_saxon,
    patron_transaction_overdue_event_sion,
    patron_transaction_overdue_event_martigny,
):
    """Test patron transaction event permissions class."""

    ptre_martigny = patron_transaction_overdue_event_martigny
    ptre_saxon = patron_transaction_overdue_event_saxon
    ptre_sion = patron_transaction_overdue_event_sion

    # Anonymous user :: all operation disallowed
    identity_changed.send(current_app._get_current_object(), identity=AnonymousIdentity())
    check_permission(
        PatronTransactionEventPermissionPolicy,
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
        PatronTransactionEventPermissionPolicy,
        {
            "search": False,
            "read": False,
            "create": False,
            "update": False,
            "delete": False,
        },
        ptre_martigny,
    )

    # Patron user :: could search any, could read own pttr
    login_user(patron_martigny.user)
    check_permission(PatronTransactionEventPermissionPolicy, {"create": False}, {})
    check_permission(
        PatronTransactionEventPermissionPolicy,
        {
            "search": True,
            "read": True,
            "create": False,
            "update": False,
            "delete": False,
        },
        ptre_martigny,
    )
    check_permission(
        PatronTransactionEventPermissionPolicy,
        {
            "read": False,
        },
        ptre_sion,
    )

    # Librarian with specific role
    #     - search: any pttr
    #     - other operations : allowed for pttr of its own organisation
    login_user(librarian_martigny.user)
    check_permission(
        PatronTransactionEventPermissionPolicy,
        {"search": True, "read": True, "create": True, "update": True, "delete": True},
        ptre_martigny,
    )
    check_permission(
        PatronTransactionEventPermissionPolicy,
        {"search": True, "read": True, "create": True, "update": True, "delete": True},
        ptre_saxon,
    )
    check_permission(
        PatronTransactionEventPermissionPolicy,
        {
            "search": True,
            "read": False,
            "create": False,
            "update": False,
            "delete": False,
        },
        ptre_sion,
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
        PatronTransactionEventPermissionPolicy,
        {
            "search": True,
            "read": True,
            "create": False,
            "update": False,
            "delete": False,
        },
        ptre_saxon,
    )
    check_permission(
        PatronTransactionEventPermissionPolicy,
        {
            "search": True,
            "read": False,
            "create": False,
            "update": False,
            "delete": False,
        },
        ptre_sion,
    )

    # reset the librarian
    librarian_martigny["roles"] = original_roles
    librarian_martigny.update(librarian_martigny, dbcommit=True, reindex=True)
    PatronsSearch.flush_and_refresh()
