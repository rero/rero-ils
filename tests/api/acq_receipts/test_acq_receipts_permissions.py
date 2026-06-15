# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

from unittest import mock

from flask import current_app
from flask_principal import AnonymousIdentity, identity_changed
from flask_security import login_user

from rero_ils.modules.acquisition.acq_orders.models import AcqOrderStatus
from rero_ils.modules.acquisition.acq_receipts.permissions import (
    AcqReceiptPermissionPolicy,
)
from tests.utils import check_permission


def test_receipts_permissions(
    patron_martigny,
    librarian_martigny,
    librarian2_martigny,
    system_librarian_martigny,
    org_martigny,
    vendor2_martigny,
    acq_receipt_fiction_sion,
    acq_receipt_fiction_saxon,
    acq_receipt_fiction_martigny,
    acq_receipt_line_1_fiction_martigny,
    acq_receipt_line_fiction_saxon,
):
    """Test receipt permissions class."""

    # Anonymous user & Patron :: None action allowed
    identity_changed.send(current_app._get_current_object(), identity=AnonymousIdentity())
    check_permission(
        AcqReceiptPermissionPolicy,
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
        AcqReceiptPermissionPolicy,
        {
            "search": False,
            "read": False,
            "create": False,
            "update": False,
            "delete": False,
        },
        acq_receipt_fiction_martigny,
    )

    # As staff member without any specific access :
    #   - None action allowed
    #   - except read record of its own library (pro_read_only)
    login_user(librarian2_martigny.user)
    check_permission(
        AcqReceiptPermissionPolicy,
        {
            "search": True,
            "read": True,
            "create": False,
            "update": False,
            "delete": False,
        },
        acq_receipt_fiction_martigny,
    )
    check_permission(
        AcqReceiptPermissionPolicy,
        {
            "search": True,
            "read": False,
            "create": False,
            "update": False,
            "delete": False,
        },
        acq_receipt_fiction_sion,
    )

    # As staff member with "library-administration" role :
    #   - Search :: everything
    #   - Read :: record of its own library
    #   - Create/Update/Delete :: record of its own library
    login_user(librarian_martigny.user)
    check_permission(
        AcqReceiptPermissionPolicy,
        {"search": True, "read": True, "create": True, "update": True, "delete": True},
        acq_receipt_fiction_martigny,
    )
    check_permission(
        AcqReceiptPermissionPolicy,
        {
            "search": True,
            "read": False,
            "create": False,
            "update": False,
            "delete": False,
        },
        acq_receipt_fiction_saxon,
    )

    # As staff member with "full_permissions" role :
    #   - Search :: everything
    #   - Read :: record of its own organisation
    #   - Create/Update/Delete :: record of its own organisation
    login_user(system_librarian_martigny.user)
    check_permission(
        AcqReceiptPermissionPolicy,
        {"search": True, "read": True, "create": True, "update": True, "delete": True},
        acq_receipt_fiction_saxon,
    )
    check_permission(
        AcqReceiptPermissionPolicy,
        {
            "search": True,
            "read": False,
            "create": False,
            "update": False,
            "delete": False,
        },
        acq_receipt_fiction_sion,
    )

    # Special case !!! An acquisition receipt linked to a closed budget
    # should be considerate as roll-overed and can't be updated.
    with mock.patch("rero_ils.modules.acquisition.acq_receipts.api.AcqReceipt.is_active", False):
        check_permission(
            AcqReceiptPermissionPolicy,
            {
                "search": True,
                "read": True,
                "create": False,
                "update": False,
                "delete": False,
            },
            acq_receipt_fiction_martigny,
        )

    with mock.patch(
        "rero_ils.modules.acquisition.acq_orders.api.AcqOrder.get_status_by_pid",
        mock.MagicMock(return_value=AcqOrderStatus.CANCELLED),
    ):
        check_permission(
            AcqReceiptPermissionPolicy,
            {
                "search": True,
                "read": True,
                "create": True,
                "update": False,
                "delete": False,
            },
            acq_receipt_fiction_martigny,
        )
    with mock.patch(
        "rero_ils.modules.acquisition.acq_orders.api.AcqOrder.get_status_by_pid",
        mock.MagicMock(return_value=AcqOrderStatus.PENDING),
    ):
        check_permission(
            AcqReceiptPermissionPolicy,
            {
                "search": True,
                "read": True,
                "create": True,
                "update": False,
                "delete": False,
            },
            acq_receipt_fiction_martigny,
        )
    with mock.patch(
        "rero_ils.modules.acquisition.acq_orders.api.AcqOrder.get_status_by_pid",
        mock.MagicMock(return_value=AcqOrderStatus.ORDERED),
    ):
        check_permission(
            AcqReceiptPermissionPolicy,
            {
                "search": True,
                "read": True,
                "create": True,
                "update": True,
                "delete": False,
            },
            acq_receipt_fiction_martigny,
        )
    with mock.patch(
        "rero_ils.modules.acquisition.acq_orders.api.AcqOrder.get_status_by_pid",
        mock.MagicMock(return_value=AcqOrderStatus.PARTIALLY_RECEIVED),
    ):
        check_permission(
            AcqReceiptPermissionPolicy,
            {
                "search": True,
                "read": True,
                "create": True,
                "update": True,
                "delete": True,
            },
            acq_receipt_fiction_martigny,
        )
    with mock.patch(
        "rero_ils.modules.acquisition.acq_orders.api.AcqOrder.get_status_by_pid",
        mock.MagicMock(return_value=AcqOrderStatus.RECEIVED),
    ):
        check_permission(
            AcqReceiptPermissionPolicy,
            {
                "search": True,
                "read": True,
                "create": True,
                "update": True,
                "delete": True,
            },
            acq_receipt_fiction_martigny,
        )
