# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Permissions for items."""

from invenio_access import action_factory

from rero_ils.modules.permissions import (
    AllowedByAction,
    AllowedByActionRestrictByManageableLibrary,
    RecordPermissionPolicy,
)

# Specific action about items
late_issue_management = action_factory("late-issue-management")

# Actions to control Items policies for CRUD operations
search_action = action_factory("item-search")
read_action = action_factory("item-read")
create_action = action_factory("item-create")
update_action = action_factory("item-update")
delete_action = action_factory("item-delete")
access_action = action_factory("item-access")


class ItemPermissionPolicy(RecordPermissionPolicy):
    """Item Permission Policy used by the CRUD operations."""

    can_search = [AllowedByAction(search_action)]
    can_read = [AllowedByAction(read_action)]
    can_create = [AllowedByActionRestrictByManageableLibrary(create_action)]
    can_update = [AllowedByActionRestrictByManageableLibrary(update_action)]
    can_delete = [AllowedByActionRestrictByManageableLibrary(delete_action)]
