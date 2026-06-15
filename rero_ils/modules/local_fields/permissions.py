# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Permissions of Local field."""

from flask import g
from invenio_access import action_factory

from rero_ils.modules.permissions import (
    AllowedByAction,
    LibraryNeed,
    OrganisationNeed,
    RecordPermissionPolicy,
)
from rero_ils.modules.utils import extracted_data_from_ref

# Actions to control "local field" policies for CRUD operations
search_action = action_factory("lofi-search")
read_action = action_factory("lofi-read")
create_action = action_factory("lofi-create")
update_action = action_factory("lofi-update")
delete_action = action_factory("lofi-delete")
access_action = action_factory("lofi-access")


class AllowedByActionRestrictByLocalFieldParent(AllowedByAction):
    """Allow editing a local field based on its parent resource.

    The local field's organisation must match the user's organisation, so users
    cannot edit local fields on resources belonging to another organisation.
    When the parent resource is library-scoped (item or holding), the parent's
    library must additionally be one of the user's manageable libraries.
    """

    def needs(self, record=None, *args, **kwargs):
        """Allows the given action.

        :param record: the local field record to check.
        :param args: extra arguments.
        :param kwargs: extra named arguments.
        :returns: a list of Needs to validate access.
        """
        if record:
            if OrganisationNeed(record.organisation_pid) not in g.identity.provides:
                return []
            parent = extracted_data_from_ref(record.get("parent"), data="record")
            if library_pid := getattr(parent, "library_pid", None):
                if LibraryNeed(library_pid) not in g.identity.provides:
                    return []
        return super().needs(record, **kwargs)


class LocalFieldPermissionPolicy(RecordPermissionPolicy):
    """LocalField Permission Policy used by the CRUD operations."""

    can_search = [AllowedByAction(search_action)]
    can_read = [AllowedByAction(read_action)]
    can_create = [AllowedByActionRestrictByLocalFieldParent(create_action)]
    can_update = [AllowedByActionRestrictByLocalFieldParent(update_action)]
    can_delete = [AllowedByActionRestrictByLocalFieldParent(delete_action)]
