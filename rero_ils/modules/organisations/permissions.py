# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Permissions for organisations."""

from invenio_access import action_factory

from rero_ils.modules.permissions import (
    AllowedByAction,
    AllowedByActionRestrictByOrganisation,
    RecordPermissionPolicy,
)

# Actions to control Organisation policies
search_action = action_factory("org-search")
read_action = action_factory("org-read")
create_action = action_factory("org-create")
update_action = action_factory("org-update")
delete_action = action_factory("org-delete")
access_action = action_factory("org-access")


class OrganisationPermissionPolicy(RecordPermissionPolicy):
    """Organisation Permission Policy used by the CRUD operations."""

    can_search = [AllowedByAction(search_action)]
    can_read = [AllowedByActionRestrictByOrganisation(read_action)]
    can_create = [AllowedByAction(create_action)]
    can_update = [AllowedByActionRestrictByOrganisation(update_action)]
    can_delete = [AllowedByAction(delete_action)]
