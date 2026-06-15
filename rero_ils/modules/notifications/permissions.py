# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Permissions for notifications."""

from invenio_access import action_factory

from rero_ils.modules.permissions import (
    AllowedByAction,
    AllowedByActionRestrictByManageableLibrary,
    AllowedByActionRestrictByOwnerOrOrganisation,
    RecordPermissionPolicy,
)

# Actions to control Items policies for CRUD operations
search_action = action_factory("notif-search")
read_action = action_factory("notif-read")
create_action = action_factory("notif-create")
update_action = action_factory("notif-update")
delete_action = action_factory("notif-delete")
access_action = action_factory("notif-access")


class NotificationPermissionPolicy(RecordPermissionPolicy):
    """Notification Permission Policy used by the CRUD operations."""

    # Some notifications subclasses have a library_pid, some have not.
    # in the second case, if we return `None` the permission may be
    # allowed if user has required ActionNeed, but we won't ; so return
    # a "dummy" value to always disallow the operation if a notification
    # don't have the `library_pid` property.

    can_search = [AllowedByAction(search_action)]
    can_read = [AllowedByActionRestrictByOwnerOrOrganisation(read_action)]
    can_create = [
        AllowedByActionRestrictByManageableLibrary(
            create_action,
            callback=lambda rec: getattr(rec, "library_pid", "unavailable_data"),
        )
    ]
    can_update = [
        AllowedByActionRestrictByManageableLibrary(
            update_action,
            callback=lambda rec: getattr(rec, "library_pid", "unavailable_data"),
        )
    ]
    can_delete = [
        AllowedByActionRestrictByManageableLibrary(
            delete_action,
            callback=lambda rec: getattr(rec, "library_pid", "unavailable_data"),
        )
    ]
