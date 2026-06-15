# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Permissions for item types."""

from invenio_access import action_factory

from rero_ils.modules.permissions import (
    AllowedByAction,
    AllowedByActionRestrictByOrganisation,
    RecordPermissionPolicy,
)

search_action = action_factory("itty-search")
read_action = action_factory("itty-read")
create_action = action_factory("itty-create")
update_action = action_factory("itty-update")
delete_action = action_factory("itty-delete")
access_action = action_factory("itty-access")


class ItemTypePermissionPolicy(RecordPermissionPolicy):
    """Patron Type Permission Policy used by the CRUD operations."""

    can_search = [AllowedByAction(search_action)]
    can_read = [AllowedByActionRestrictByOrganisation(read_action)]
    can_create = [AllowedByActionRestrictByOrganisation(create_action)]
    can_update = [AllowedByActionRestrictByOrganisation(update_action)]
    can_delete = [AllowedByActionRestrictByOrganisation(delete_action)]
