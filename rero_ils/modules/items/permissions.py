# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Permissions for items."""

from invenio_access import action_factory, any_user
from invenio_records_permissions.generators import Generator

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


class DisallowIfCannotEdit(Generator):
    """Disallow the operation when the record cannot be edited (e.g. harvested)."""

    def excludes(self, record=None, **kwargs):
        """Disallow operation check.

        :param record: the record to check.
        :param kwargs: extra named arguments.
        :returns: a list of Needs to disable access.
        """
        return [any_user] if record and not record.can_edit else []


class ItemPermissionPolicy(RecordPermissionPolicy):
    """Item Permission Policy used by the CRUD operations."""

    can_search = [AllowedByAction(search_action)]
    can_read = [AllowedByAction(read_action)]
    can_create = [AllowedByActionRestrictByManageableLibrary(create_action)]
    can_update = [AllowedByActionRestrictByManageableLibrary(update_action), DisallowIfCannotEdit()]
    can_delete = [AllowedByActionRestrictByManageableLibrary(delete_action), DisallowIfCannotEdit()]
