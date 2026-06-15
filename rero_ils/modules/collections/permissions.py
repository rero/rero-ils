# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Collection permissions."""

from invenio_access import action_factory

from rero_ils.modules.permissions import (
    AllowedByAction,
    AllowedByActionRestrictByManageableLibrary,
    AllowedByActionRestrictByOrganisation,
    RecordPermissionPolicy,
)

# Actions to control Items policies for CRUD operations
search_action = action_factory("coll-search")
read_action = action_factory("coll-read")
create_action = action_factory("coll-create")
update_action = action_factory("coll-update")
delete_action = action_factory("coll-delete")
access_action = action_factory("coll-access")


def get_libraries(collection):
    """Get a callback function to return library pids."""
    return getattr(collection, "library_pids", None)


class CollectionPermissionPolicy(RecordPermissionPolicy):
    """Collection Permission Policy used by the CRUD operations."""

    can_search = [AllowedByAction(search_action)]
    can_read = [AllowedByActionRestrictByOrganisation(read_action)]
    can_create = [AllowedByActionRestrictByManageableLibrary(create_action, callback=get_libraries)]
    can_update = [AllowedByActionRestrictByManageableLibrary(update_action, callback=get_libraries)]
    can_delete = [AllowedByActionRestrictByManageableLibrary(delete_action, callback=get_libraries)]
