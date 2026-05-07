# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2020 RERO
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from unittest import mock

from flask import current_app
from flask_principal import AnonymousIdentity, identity_changed
from flask_security import login_user

from rero_ils.modules.local_fields.permissions import LocalFieldPermissionPolicy
from rero_ils.modules.patrons.api import Patron, PatronsSearch
from tests.utils import check_permission


@mock.patch.object(Patron, "_extensions", [])
def test_local_fields_permissions(
    local_field_martigny,
    local_field_3_martigny,
    librarian_martigny,
    librarian_saxon,
    local_field_sion,
):
    """Test item permissions class."""

    # Anonymous user & Patron user
    #  - search/read any local fields are allowed.
    #  - create/update/delete operations are disallowed.
    identity_changed.send(current_app._get_current_object(), identity=AnonymousIdentity())
    check_permission(
        LocalFieldPermissionPolicy,
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
        LocalFieldPermissionPolicy,
        {
            "search": True,
            "read": True,
            "create": False,
            "update": False,
            "delete": False,
        },
        local_field_martigny,
    )

    # Librarian of `lib_martigny` (org Martigny)
    #   - search/read: any local fields, including those of other organisations.
    #   - create/update/delete: allowed for any local field of the
    #     organisation when the parent resource has no library (e.g. document)
    #     or has a library managed by the user.
    #   - all edit operations denied for local fields of another organisation.
    login_user(librarian_martigny.user)
    check_permission(
        LocalFieldPermissionPolicy,
        {"search": True, "read": True, "create": True, "update": True, "delete": True},
        local_field_martigny,
    )
    check_permission(
        LocalFieldPermissionPolicy,
        {"search": True, "read": True, "create": True, "update": True, "delete": True},
        local_field_3_martigny,
    )
    check_permission(
        LocalFieldPermissionPolicy,
        {
            "search": True,
            "read": True,
            "create": False,
            "update": False,
            "delete": False,
        },
        local_field_sion,
    )

    # Librarian of `lib_saxon` (same organisation, different library)
    #   - create/update/delete: allowed when the parent has no library
    #     (document case) but denied when the parent's library is not
    #     managed by the user.
    login_user(librarian_saxon.user)
    check_permission(
        LocalFieldPermissionPolicy,
        {"search": True, "read": True, "create": True, "update": True, "delete": True},
        local_field_martigny,
    )
    check_permission(
        LocalFieldPermissionPolicy,
        {
            "search": True,
            "read": True,
            "create": False,
            "update": False,
            "delete": False,
        },
        local_field_3_martigny,
    )

    # Librarian without `lofi-*` action role
    #   - search/read: any local field.
    #   - create/update/delete: disallowed because `pro_user_manager` is not
    #     part of the roles granted on lofi-create/update/delete actions.
    original_roles = librarian_martigny.get("roles", [])
    librarian_martigny["roles"] = ["pro_user_manager"]
    librarian_martigny.update(librarian_martigny, dbcommit=True, reindex=True)
    PatronsSearch.flush_and_refresh()

    login_user(librarian_martigny.user)  # to refresh identity !
    check_permission(
        LocalFieldPermissionPolicy,
        {
            "search": True,
            "read": True,
            "create": False,
            "update": False,
            "delete": False,
        },
        local_field_martigny,
    )

    # reset the librarian
    librarian_martigny["roles"] = original_roles
    librarian_martigny.update(librarian_martigny, dbcommit=True, reindex=True)
    PatronsSearch.flush_and_refresh()
