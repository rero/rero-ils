# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Permissions for Acquisition order."""

from invenio_access import action_factory

from rero_ils.modules.permissions import (
    AllowedByAction,
    AllowedByActionRestrictByManageableLibrary,
    DisallowedIfRollovered,
    RecordPermissionPolicy,
)

from .api import AcqOrder

# Actions to control acquisition orders resource policies
search_action = action_factory("acor-search")
read_action = action_factory("acor-read")
create_action = action_factory("acor-create")
update_action = action_factory("acor-update")
delete_action = action_factory("acor-delete")
access_action = action_factory("acor-access")


class AcqOrderPermissionPolicy(RecordPermissionPolicy):
    """Acquisition order Permission Policy used by the CRUD operations."""

    can_search = [AllowedByAction(search_action)]
    can_read = [AllowedByActionRestrictByManageableLibrary(read_action)]
    can_create = [
        AllowedByActionRestrictByManageableLibrary(create_action),
        DisallowedIfRollovered(AcqOrder),
    ]
    can_update = [
        AllowedByActionRestrictByManageableLibrary(update_action),
        DisallowedIfRollovered(AcqOrder),
    ]
    can_delete = [
        AllowedByActionRestrictByManageableLibrary(delete_action),
        DisallowedIfRollovered(AcqOrder),
    ]
