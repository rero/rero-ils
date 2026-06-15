# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

from unittest import mock

from flask import current_app
from flask_principal import AnonymousIdentity, identity_changed
from flask_security import login_user

from rero_ils.modules.documents.permissions import DocumentPermissionPolicy
from rero_ils.modules.patrons.api import Patron, PatronsSearch
from tests.utils import check_permission


@mock.patch.object(Patron, "_extensions", [])
def test_documents_permissions(patron_martigny, librarian_martigny, document):
    """Test documents permissions class."""
    # Anonymous user & Patron user
    #  - search/read any document are allowed.
    #  - create/update/delete operations are disallowed.
    identity_changed.send(current_app._get_current_object(), identity=AnonymousIdentity())
    check_permission(
        DocumentPermissionPolicy,
        {
            "search": True,
            "read": True,
            "create": False,
            "update": False,
            "delete": False,
        },
        None,
    )
    check_permission(
        DocumentPermissionPolicy,
        {
            "search": True,
            "read": True,
            "create": False,
            "update": False,
            "delete": False,
        },
        document,
    )
    login_user(patron_martigny.user)
    check_permission(DocumentPermissionPolicy, {"create": False}, {})
    check_permission(
        DocumentPermissionPolicy,
        {
            "search": True,
            "read": True,
            "create": False,
            "update": False,
            "delete": False,
        },
        document,
    )

    # Librarian with specific role
    #     - search/read: any document
    #     - create/update/delete: allowed for any document
    login_user(librarian_martigny.user)
    check_permission(
        DocumentPermissionPolicy,
        {"search": True, "read": True, "create": True, "update": True, "delete": True},
        document,
    )

    # Librarian without specific role
    #   - search/read: any document
    #   - create/update/delete: disallowed for any document !!
    original_roles = librarian_martigny.get("roles", [])
    librarian_martigny["roles"] = ["pro_circulation_manager"]
    librarian_martigny.update(librarian_martigny, dbcommit=True, reindex=True)
    PatronsSearch.flush_and_refresh()

    login_user(librarian_martigny.user)  # to refresh identity !
    check_permission(
        DocumentPermissionPolicy,
        {
            "search": True,
            "read": True,
            "create": False,
            "update": False,
            "delete": False,
        },
        document,
    )

    # reset the librarian
    librarian_martigny["roles"] = original_roles
    librarian_martigny.update(librarian_martigny, dbcommit=True, reindex=True)
    PatronsSearch.flush_and_refresh()

    # Test if the document cannot be edited (harvested documents, ...)
    with mock.patch("rero_ils.modules.documents.api.Document.can_edit", False):
        check_permission(
            DocumentPermissionPolicy,
            {
                "search": True,
                "read": True,
                "create": False,
                "update": False,
                "delete": False,
            },
            document,
        )
