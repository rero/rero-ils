# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Permissions for Acquisition receipt."""

from invenio_access import action_factory

from rero_ils.modules.acquisition.acq_orders.models import AcqOrderStatus
from rero_ils.modules.permissions import (
    AllowedByAction,
    AllowedByActionRestrictByManageableLibrary,
    DisallowedByOrderStatus,
    DisallowedIfRollovered,
    RecordPermissionPolicy,
)

from .api import AcqReceipt

# Actions to control acquisition receipts resource policies
search_action = action_factory("acre-search")
read_action = action_factory("acre-read")
create_action = action_factory("acre-create")
update_action = action_factory("acre-update")
delete_action = action_factory("acre-delete")
access_action = action_factory("acre-access")


class AcqReceiptPermissionPolicy(RecordPermissionPolicy):
    """Acquisition receipt Permission Policy used by the CRUD operations."""

    can_search = [AllowedByAction(search_action)]
    can_read = [AllowedByActionRestrictByManageableLibrary(read_action)]
    can_create = [
        AllowedByActionRestrictByManageableLibrary(create_action),
        DisallowedIfRollovered(AcqReceipt),
    ]
    can_update = [
        AllowedByActionRestrictByManageableLibrary(update_action),
        DisallowedIfRollovered(AcqReceipt),
        DisallowedByOrderStatus(
            AcqReceipt,
            [
                AcqOrderStatus.PARTIALLY_RECEIVED,
                AcqOrderStatus.RECEIVED,
                AcqOrderStatus.ORDERED,
            ],
        ),
    ]
    can_delete = [
        AllowedByActionRestrictByManageableLibrary(delete_action),
        DisallowedIfRollovered(AcqReceipt),
        DisallowedByOrderStatus(
            record_cls=AcqReceipt,
            allowed_statuses=[
                AcqOrderStatus.PARTIALLY_RECEIVED,
                AcqOrderStatus.RECEIVED,
            ],
        ),
    ]
