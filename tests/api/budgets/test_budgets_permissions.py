# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

from flask import current_app
from flask_principal import AnonymousIdentity, identity_changed
from flask_security import login_user

from rero_ils.modules.acquisition.budgets.permissions import BudgetPermissionPolicy
from tests.utils import check_permission


def test_budget_permissions(patron_martigny, librarian_martigny, budget_2018_martigny, budget_2020_sion):
    """Test budget permissions class."""

    # Anonymous user
    identity_changed.send(current_app._get_current_object(), identity=AnonymousIdentity())
    check_permission(
        BudgetPermissionPolicy,
        {
            "search": False,
            "read": False,
            "create": False,
            "update": False,
            "delete": False,
        },
        {},
    )

    # Patron :: can't operate any operation about Budget
    login_user(patron_martigny.user)
    check_permission(
        BudgetPermissionPolicy,
        {
            "search": False,
            "read": False,
            "create": False,
            "update": False,
            "delete": False,
        },
        budget_2018_martigny,
    )

    # Staff members :: can only search and read (only org record)
    login_user(librarian_martigny.user)
    check_permission(
        BudgetPermissionPolicy,
        {
            "search": True,
            "read": True,
            "create": False,
            "update": False,
            "delete": False,
        },
        budget_2018_martigny,
    )
    check_permission(
        BudgetPermissionPolicy,
        {
            "search": True,
            "read": False,
            "create": False,
            "update": False,
            "delete": False,
        },
        budget_2020_sion,
    )
