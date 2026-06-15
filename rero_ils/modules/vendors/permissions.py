# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Permissions for vendors."""

from invenio_access import action_factory

from rero_ils.modules.permissions import (
    AllowedByAction,
    AllowedByActionRestrictByOrganisation,
    RecordPermissionPolicy,
)

search_action = action_factory("vndr-search")
read_action = action_factory("vndr-read")
create_action = action_factory("vndr-create")
update_action = action_factory("vndr-update")
delete_action = action_factory("vndr-delete")
access_action = action_factory("vndr-access")


class VendorPermissionPolicy(RecordPermissionPolicy):
    """Patron Type Permission Policy used by the CRUD operations."""

    can_search = [AllowedByAction(search_action)]
    can_read = [AllowedByActionRestrictByOrganisation(read_action)]
    can_create = [AllowedByActionRestrictByOrganisation(create_action)]
    can_update = [AllowedByActionRestrictByOrganisation(update_action)]
    can_delete = [AllowedByActionRestrictByOrganisation(delete_action)]
