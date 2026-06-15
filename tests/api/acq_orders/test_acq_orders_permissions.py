# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

from unittest import mock

from flask import current_app
from flask_principal import AnonymousIdentity, identity_changed
from flask_security import login_user

from rero_ils.modules.acquisition.acq_orders.permissions import AcqOrderPermissionPolicy
from tests.utils import check_permission


def test_orders_permissions(
    patron_martigny,
    librarian_martigny,
    librarian2_martigny,
    system_librarian_martigny,
    org_martigny,
    vendor2_martigny,
    acq_order_fiction_sion,
    acq_order_fiction_saxon,
    acq_order_fiction_martigny,
):
    """Test orders permissions class."""

    # Anonymous user & Patron :: None action allowed
    identity_changed.send(current_app._get_current_object(), identity=AnonymousIdentity())
    check_permission(
        AcqOrderPermissionPolicy,
        {
            "search": False,
            "read": False,
            "create": False,
            "update": False,
            "delete": False,
        },
        {},
    )
    login_user(patron_martigny.user)
    check_permission(
        AcqOrderPermissionPolicy,
        {
            "search": False,
            "read": False,
            "create": False,
            "update": False,
            "delete": False,
        },
        acq_order_fiction_martigny,
    )

    # As staff member without any specific access :
    #   - None action allowed
    #   - except read record of its own library (pro_read_only)
    login_user(librarian2_martigny.user)
    check_permission(
        AcqOrderPermissionPolicy,
        {
            "search": True,
            "read": True,
            "create": False,
            "update": False,
            "delete": False,
        },
        acq_order_fiction_martigny,
    )
    check_permission(
        AcqOrderPermissionPolicy,
        {
            "search": True,
            "read": False,
            "create": False,
            "update": False,
            "delete": False,
        },
        acq_order_fiction_sion,
    )

    # As staff member with "library-administration" role :
    #   - Search :: everything
    #   - Read :: record of its own library
    #   - Create/Update/Delete :: record of its own library
    login_user(librarian_martigny.user)
    check_permission(
        AcqOrderPermissionPolicy,
        {"search": True, "read": True, "create": True, "update": True, "delete": True},
        acq_order_fiction_martigny,
    )
    check_permission(
        AcqOrderPermissionPolicy,
        {
            "search": True,
            "read": False,
            "create": False,
            "update": False,
            "delete": False,
        },
        acq_order_fiction_saxon,
    )

    # As staff member with "full_permissions" role :
    #   - Search :: everything
    #   - Read :: record of its own organisation
    #   - Create/Update/Delete :: record of its own organisation
    login_user(system_librarian_martigny.user)
    check_permission(
        AcqOrderPermissionPolicy,
        {"search": True, "read": True, "create": True, "update": True, "delete": True},
        acq_order_fiction_saxon,
    )
    check_permission(
        AcqOrderPermissionPolicy,
        {
            "search": True,
            "read": False,
            "create": False,
            "update": False,
            "delete": False,
        },
        acq_order_fiction_sion,
    )

    # Special case !!! An acquisition order linked to a closed budget
    # should be considerate as roll-overed and can't be updated.
    with mock.patch("rero_ils.modules.acquisition.acq_orders.api.AcqOrder.is_active", False):
        check_permission(
            AcqOrderPermissionPolicy,
            {
                "search": True,
                "read": True,
                "create": False,
                "update": False,
                "delete": False,
            },
            acq_order_fiction_martigny,
        )
