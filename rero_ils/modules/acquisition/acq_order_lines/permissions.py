# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Permissions for Acquisition order line."""

from invenio_access import action_factory

from rero_ils.modules.acquisition.acq_orders.models import AcqOrderStatus
from rero_ils.modules.permissions import (
    AllowedByAction,
    AllowedByActionRestrictByManageableLibrary,
    DisallowedByOrderStatus,
    DisallowedIfRollovered,
    RecordPermissionPolicy,
)

from .api import AcqOrderLine

# Actions to control acquisition order lines resource policies
search_action = action_factory("acol-search")
read_action = action_factory("acol-read")
create_action = action_factory("acol-create")
update_action = action_factory("acol-update")
delete_action = action_factory("acol-delete")
access_action = action_factory("acol-access")


class AcqOrderLinePermissionPolicy(RecordPermissionPolicy):
    """Acquisition order line permission policy used by the CRUD operations."""

    can_search = [AllowedByAction(search_action)]
    can_read = [AllowedByActionRestrictByManageableLibrary(read_action)]
    can_create = [
        AllowedByActionRestrictByManageableLibrary(create_action),
        DisallowedIfRollovered(AcqOrderLine),
    ]
    can_update = [
        AllowedByActionRestrictByManageableLibrary(update_action),
        DisallowedIfRollovered(AcqOrderLine),
        DisallowedByOrderStatus(
            AcqOrderLine,
            [
                AcqOrderStatus.CANCELLED,
                AcqOrderStatus.PENDING,
                AcqOrderStatus.ORDERED,
                AcqOrderStatus.PARTIALLY_RECEIVED,
            ],
        ),
    ]
    can_delete = [
        AllowedByActionRestrictByManageableLibrary(delete_action),
        DisallowedIfRollovered(AcqOrderLine),
        DisallowedByOrderStatus(
            record_cls=AcqOrderLine,
            allowed_statuses=[AcqOrderStatus.CANCELLED, AcqOrderStatus.PENDING],
        ),
    ]
