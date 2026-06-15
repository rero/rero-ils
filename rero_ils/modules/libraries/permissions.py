# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Permissions for libraries."""

from invenio_access import action_factory

from rero_ils.modules.permissions import (
    AllowedByAction,
    AllowedByActionRestrictByManageableLibrary,
    AllowedByActionRestrictByOrganisation,
    RecordPermissionPolicy,
)

# Actions to control library policy
search_action = action_factory("lib-search")
read_action = action_factory("lib-read")
create_action = action_factory("lib-create")
update_action = action_factory("lib-update")
delete_action = action_factory("lib-delete")
access_action = action_factory("lib-access")


def get_library_pid(record):
    """Get the library pid from the record."""
    return record.get("pid") if record else None


class LibraryPermissionPolicy(RecordPermissionPolicy):
    """Library Permission Policy used by the CRUD operations."""

    can_search = [AllowedByAction(search_action)]
    can_read = [AllowedByActionRestrictByOrganisation(read_action)]
    can_create = [AllowedByActionRestrictByManageableLibrary(create_action, get_library_pid)]
    can_update = [AllowedByActionRestrictByManageableLibrary(update_action, get_library_pid)]
    can_delete = [AllowedByActionRestrictByManageableLibrary(delete_action, get_library_pid)]
