# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

from flask import current_app
from flask_principal import AnonymousIdentity, identity_changed
from flask_security import login_user

from rero_ils.modules.ill_requests.permissions import ILLRequestPermissionPolicy
from tests.utils import check_permission


def test_ill_requests_permissions(
    patron_martigny,
    librarian_martigny,
    system_librarian_martigny,
    ill_request_martigny,
    ill_request_sion,
    org_martigny,
):
    """Test ill requests permissions class."""
    # Anonymous user
    identity_changed.send(current_app._get_current_object(), identity=AnonymousIdentity())
    check_permission(
        ILLRequestPermissionPolicy,
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
        ILLRequestPermissionPolicy,
        {
            "search": True,
            "read": True,
            "create": True,
            "update": False,
            "delete": False,
        },
        ill_request_martigny,
    )
    check_permission(
        ILLRequestPermissionPolicy,
        {
            "search": True,
            "read": False,
            "create": True,
            "update": False,
            "delete": False,
        },
        ill_request_sion,
    )

    # Librarian without correct role
    #     - can : search, read (own organisation), create
    #     - update : only request for its own organisation
    #     - delete : disallowed (missing ActionNeed)
    login_user(librarian_martigny.user)
    check_permission(
        ILLRequestPermissionPolicy,
        {"search": True, "read": True, "create": True, "update": True, "delete": False},
        ill_request_martigny,
    )
    check_permission(
        ILLRequestPermissionPolicy,
        {
            "search": True,
            "read": False,
            "create": True,
            "update": False,
            "delete": False,
        },
        ill_request_sion,
    )
