# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Permissions for holdings."""

from invenio_access import action_factory, any_user
from invenio_records_permissions.generators import Generator

from rero_ils.modules.permissions import (
    AllowedByAction,
    AllowedByActionRestrictByManageableLibrary,
    RecordPermissionPolicy,
)

# Actions to control Holdings policies for CRUD operations
search_action = action_factory("hold-search")
read_action = action_factory("hold-read")
create_action = action_factory("hold-create")
update_action = action_factory("hold-update")
delete_action = action_factory("hold-delete")
access_action = action_factory("hold-access")


class DisallowIfNotSerialHolding(Generator):
    """Disallow any operation if record isn't a serial record."""

    def excludes(self, record=None, **kwargs):
        """Disallow operation check.

        :param record; the record to check.
        :param kwargs: extra named arguments.
        :returns: a list of Needs to disable access.
        """
        return [any_user] if record and not record.is_serial else []


class HoldingsPermissionPolicy(RecordPermissionPolicy):
    """Holdings Permission Policy used by the CRUD operations."""

    can_search = [AllowedByAction(search_action)]
    can_read = [AllowedByAction(read_action)]
    can_create = [
        AllowedByActionRestrictByManageableLibrary(create_action),
        DisallowIfNotSerialHolding(),
    ]
    can_update = [
        AllowedByActionRestrictByManageableLibrary(update_action),
        DisallowIfNotSerialHolding(),
    ]
    can_delete = [
        AllowedByActionRestrictByManageableLibrary(delete_action),
        DisallowIfNotSerialHolding(),
    ]
