# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Permissions for Acquisition account."""

from invenio_access import action_factory

from rero_ils.modules.permissions import (
    AllowedByAction,
    AllowedByActionRestrictByManageableLibrary,
    DisallowedIfRollovered,
    RecordPermissionPolicy,
)

from .api import AcqAccount

# Actions to control acquisition accounts resource policies
search_action = action_factory("acac-search")
read_action = action_factory("acac-read")
create_action = action_factory("acac-create")
update_action = action_factory("acac-update")
delete_action = action_factory("acac-delete")
access_action = action_factory("acac-access")
transfer_action = action_factory("acac-transfer")


class AcqAccountPermissionPolicy(RecordPermissionPolicy):
    """Acquisition account Permission Policy used by the CRUD operations."""

    can_search = [AllowedByAction(search_action)]
    can_read = [AllowedByActionRestrictByManageableLibrary(read_action)]
    can_create = [
        AllowedByActionRestrictByManageableLibrary(create_action),
        DisallowedIfRollovered(AcqAccount),
    ]
    can_update = [
        AllowedByActionRestrictByManageableLibrary(update_action),
        DisallowedIfRollovered(AcqAccount),
    ]
    can_delete = [
        AllowedByActionRestrictByManageableLibrary(delete_action),
        DisallowedIfRollovered(AcqAccount),
    ]
