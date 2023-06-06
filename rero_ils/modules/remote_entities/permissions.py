# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
# Copyright (C) 2019-2023 UCLouvain
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

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
