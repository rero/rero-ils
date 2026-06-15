# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

from flask import current_app
from flask_principal import AnonymousIdentity, identity_changed
from flask_security.utils import login_user

from rero_ils.modules.entities.local_entities.permissions import (
    LocalEntityPermissionPolicy,
)
from tests.utils import check_permission


def test_local_entity_permissions(
    patron_martigny,
    librarian_martigny,
    librarian2_martigny,
    system_librarian_martigny,
    local_entity_person,
):
    """Test entity permissions class."""
    permission_policy = LocalEntityPermissionPolicy

    # Anonymous user
    #   - Allow search/read actions on any local entity
    #   - Deny create/update/delete actions on any local entity
    identity_changed.send(current_app._get_current_object(), identity=AnonymousIdentity())
    check_permission(
        permission_policy,
        {
            "search": True,
            "read": True,
            "create": False,
            "update": False,
            "delete": False,
        },
        {},
    )
    # Patron user
    #   - Allow search/read actions on any local entity
    #   - Deny create/update/delete actions on any local entity
    login_user(patron_martigny.user)
    check_permission(
        permission_policy,
        {
            "search": True,
            "read": True,
            "create": False,
            "update": False,
            "delete": False,
        },
        local_entity_person,
    )
    # As staff member without `pro_entity_manager` role :
    #   - Allow search/read actions on any local entity
    #   - Deny create/update/delete actions on any local entity
    login_user(librarian2_martigny.user)
    check_permission(
        permission_policy,
        {
            "search": True,
            "read": True,
            "create": False,
            "update": False,
            "delete": False,
        },
        local_entity_person,
    )
    # As staff member with `pro_entity_manager` role :
    #   - Allow search/read actions on any local entity
    #   - Allow create/update/delete actions on any local entity
    login_user(librarian_martigny.user)
    check_permission(
        permission_policy,
        {"search": True, "read": True, "create": True, "update": True, "delete": True},
        local_entity_person,
    )
    # Full permission user
    #   - Allow search/read actions on any local entity
    #   - Allow create/update/delete actions on any local entity
    login_user(system_librarian_martigny.user)
    check_permission(
        permission_policy,
        {"search": True, "read": True, "create": True, "update": True, "delete": True},
        local_entity_person,
    )
