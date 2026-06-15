# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Permissions for ILL request."""

from invenio_access import action_factory

from rero_ils.modules.permissions import (
    AllowedByAction,
    AllowedByActionRestrictByOrganisation,
    AllowedByActionRestrictByOwnerOrOrganisation,
    RecordPermissionPolicy,
)

# Actions to control ILL request policy
search_action = action_factory("illr-search")
read_action = action_factory("illr-read")
create_action = action_factory("illr-create")
update_action = action_factory("illr-update")
delete_action = action_factory("illr-delete")
access_action = action_factory("illr-access")


class ILLRequestPermissionPolicy(RecordPermissionPolicy):
    """Library Permission Policy used by the CRUD operations."""

    can_search = [AllowedByAction(search_action)]
    can_read = [AllowedByActionRestrictByOwnerOrOrganisation(read_action)]
    can_create = [AllowedByAction(create_action)]
    can_update = [AllowedByActionRestrictByOrganisation(update_action)]
    can_delete = [AllowedByActionRestrictByOrganisation(delete_action)]
