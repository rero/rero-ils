# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Permissions for Patron transaction."""

from invenio_access import action_factory

from rero_ils.modules.permissions import (
    AllowedByAction,
    AllowedByActionRestrictByOrganisation,
    AllowedByActionRestrictByOwnerOrOrganisation,
    RecordPermissionPolicy,
)

# Actions to control patron transaction policies for CRUD operations
search_action = action_factory("pttr-search")
read_action = action_factory("pttr-read")
create_action = action_factory("pttr-create")
update_action = action_factory("pttr-update")
delete_action = action_factory("pttr-delete")
access_action = action_factory("pttr-access")


class PatronTransactionPermissionPolicy(RecordPermissionPolicy):
    """PatronTransaction permission policy used by the CRUD operations."""

    can_search = [AllowedByAction(search_action)]
    can_read = [AllowedByActionRestrictByOwnerOrOrganisation(read_action)]
    can_create = [AllowedByActionRestrictByOrganisation(create_action)]
    can_update = [AllowedByActionRestrictByOrganisation(update_action)]
    can_delete = [AllowedByActionRestrictByOrganisation(delete_action)]
