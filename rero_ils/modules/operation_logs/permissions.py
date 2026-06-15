# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Permissions of Operation log."""

from invenio_access import action_factory

from rero_ils.modules.permissions import AllowedByAction, RecordPermissionPolicy

# Actions to control operation logs policies for CRUD operations
search_action = action_factory("oplg-search")
read_action = action_factory("oplg-read")
access_action = action_factory("oplg-access")


class OperationLogPermissionPolicy(RecordPermissionPolicy):
    """Operation log Permission Policy used by the CRUD operations."""

    can_search = [AllowedByAction(search_action)]
    can_read = [AllowedByAction(read_action)]
