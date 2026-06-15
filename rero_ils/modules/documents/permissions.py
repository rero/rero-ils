# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Permissions for documents."""

from invenio_access import action_factory
from invenio_access.permissions import any_user
from invenio_records_permissions.generators import Generator

from rero_ils.modules.permissions import AllowedByAction, RecordPermissionPolicy

# Actions to control Documents policies for CRUD operations
search_action = action_factory("doc-search")
read_action = action_factory("doc-read")
create_action = action_factory("doc-create")
update_action = action_factory("doc-update")
delete_action = action_factory("doc-delete")
access_action = action_factory("doc-access")


class DisallowIfCannotEdit(Generator):
    """Disallow if the record cannot be edited due on record data."""

    def excludes(self, record=None, **kwargs):
        """Disallow operation check.

        :param record; the record to check.
        :param kwargs: extra named arguments.
        :returns: a list of Needs to disable access.
        """
        return [any_user] if record and not record.can_edit else []


class DocumentPermissionPolicy(RecordPermissionPolicy):
    """Document Permission Policy used by the CRUD operations."""

    can_search = [AllowedByAction(search_action)]
    can_read = [AllowedByAction(read_action)]
    can_create = [AllowedByAction(create_action)]
    can_update = [AllowedByAction(update_action), DisallowIfCannotEdit()]
    can_delete = [AllowedByAction(delete_action), DisallowIfCannotEdit()]
