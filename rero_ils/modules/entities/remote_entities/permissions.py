# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Permissions for `Entity` records."""

from invenio_records_permissions.generators import AnyUser

from rero_ils.modules.permissions import RecordPermissionPolicy


class RemoteEntityPermissionPolicy(RecordPermissionPolicy):
    """Entity Permission Policy used by the CRUD operations.

    Only search and read is allowed for all users.
    Other operations are denied far anybody.
    """

    can_search = [AnyUser()]
    can_read = [AnyUser()]
