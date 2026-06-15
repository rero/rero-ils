# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Permissions for locations."""

from invenio_access import action_factory

from rero_ils.modules.permissions import (
    AllowedByAction,
    AllowedByActionRestrictByManageableLibrary,
    AllowedByActionRestrictByOrganisation,
    RecordPermissionPolicy,
)

# Actions to control location policy
search_action = action_factory("loc-search")
read_action = action_factory("loc-read")
create_action = action_factory("loc-create")
update_action = action_factory("loc-update")
delete_action = action_factory("loc-delete")
access_action = action_factory("loc-access")


class LocationPermissionPolicy(RecordPermissionPolicy):
    """Location Permission Policy used by the CRUD operations."""

    can_search = [AllowedByAction(search_action)]
    can_read = [AllowedByActionRestrictByOrganisation(read_action)]
    can_create = [AllowedByActionRestrictByManageableLibrary(create_action)]
    can_update = [AllowedByActionRestrictByManageableLibrary(update_action)]
    can_delete = [AllowedByActionRestrictByManageableLibrary(delete_action)]
