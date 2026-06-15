# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Permissions for statistics configuration."""

from invenio_access import action_factory

from rero_ils.modules.permissions import (
    AllowedByAction,
    AllowedByActionRestrictByManageableLibrary,
    AllowedByActionRestrictByOrganisation,
    RecordPermissionPolicy,
)

# Actions to control statistics configuration policies for CRUD operations
search_action = action_factory("stat_cfg-search")
read_action = action_factory("stat_cfg-read")
create_action = action_factory("stat_cfg-create")
update_action = action_factory("stat_cfg-update")
delete_action = action_factory("stat_cfg-delete")
access_action = action_factory("stat_cfg-access")


class StatisticsConfigurationPermissionPolicy(RecordPermissionPolicy):
    """Statistics configuration permission policy for CRUD operations."""

    can_search = [AllowedByAction(search_action)]
    can_read = [AllowedByActionRestrictByOrganisation(read_action)]
    can_create = [AllowedByActionRestrictByOrganisation(create_action)]
    can_update = [AllowedByActionRestrictByManageableLibrary(update_action)]
    can_delete = [AllowedByActionRestrictByManageableLibrary(delete_action)]
