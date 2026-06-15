# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Permissions for `Local Entity` records."""

from invenio_access import action_factory

from rero_ils.modules.permissions import AllowedByAction, RecordPermissionPolicy

# Actions to control local entity policies for CRUD operations
search_action = action_factory("locent-search")
read_action = action_factory("locent-read")
create_action = action_factory("locent-create")
update_action = action_factory("locent-update")
delete_action = action_factory("locent-delete")
access_action = action_factory("locent-access")


class LocalEntityPermissionPolicy(RecordPermissionPolicy):
    """Local entity Permission Policy used by the CRUD operations.

    Only search and read is allowed for all users.
    Other operations are denied far anybody.
    """

    can_search = [AllowedByAction(search_action)]
    can_read = [AllowedByAction(read_action)]
    can_create = [AllowedByAction(create_action)]
    can_update = [AllowedByAction(update_action)]
    can_delete = [AllowedByAction(delete_action)]
