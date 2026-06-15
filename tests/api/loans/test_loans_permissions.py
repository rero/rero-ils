# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

from flask import current_app
from flask_principal import AnonymousIdentity, identity_changed
from flask_security import login_user

from rero_ils.modules.loans.permissions import LoanPermissionPolicy
from tests.utils import check_permission


def test_loan_permissions(patron_martigny, librarian_martigny, loan_overdue_martigny, loan_overdue_sion):
    """Test loans permissions api."""
    # Anonymous user
    identity_changed.send(current_app._get_current_object(), identity=AnonymousIdentity())
    check_permission(
        LoanPermissionPolicy,
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
    #    * can : search, read (own record), create
    #    * can't : update, delete
    login_user(patron_martigny.user)
    check_permission(
        LoanPermissionPolicy,
        {
            "search": True,
            "read": True,
            "create": False,
            "update": False,
            "delete": False,
        },
        loan_overdue_martigny,
    )
    check_permission(
        LoanPermissionPolicy,
        {
            "search": False,
            "read": False,
            "create": False,
            "update": False,
            "delete": False,
        },
        loan_overdue_sion,
    )

    # Librarian without correct role
    #     - can : search, read (own organisation), create
    #     - update, delete : disallowed (missing ActionNeed)
    login_user(librarian_martigny.user)
    check_permission(
        LoanPermissionPolicy,
        {
            "search": True,
            "read": True,
            "create": False,
            "update": False,
            "delete": False,
        },
        loan_overdue_martigny,
    )
    check_permission(
        LoanPermissionPolicy,
        {
            "search": False,
            "read": False,
            "create": False,
            "update": False,
            "delete": False,
        },
        loan_overdue_sion,
    )

    # Loan anonymized
    loan_overdue_martigny["to_anonymize"] = True
    login_user(librarian_martigny.user)
    check_permission(
        LoanPermissionPolicy,
        {
            "search": True,
            "read": False,
            "create": False,
            "update": False,
            "delete": False,
        },
        loan_overdue_martigny,
    )
