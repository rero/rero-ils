# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Circulation policies permissions."""

from invenio_access import action_factory

from rero_ils.modules.permissions import (
    AllowedByAction,
    AllowedByActionRestrictByOrganisation,
    RecordPermissionPolicy,
)

search_action = action_factory("cipo-search")
read_action = action_factory("cipo-read")
create_action = action_factory("cipo-create")
update_action = action_factory("cipo-update")
delete_action = action_factory("cipo-delete")
access_action = action_factory("cipo-access")


class CirculationPolicyPermissionPolicy(RecordPermissionPolicy):
    """Circulation policies Permission Policy used by the CRUD operations."""

    can_search = [AllowedByAction(search_action)]
    can_read = [AllowedByActionRestrictByOrganisation(read_action)]
    can_create = [AllowedByActionRestrictByOrganisation(create_action)]
    can_update = [AllowedByActionRestrictByOrganisation(update_action)]
    can_delete = [AllowedByActionRestrictByOrganisation(delete_action)]
