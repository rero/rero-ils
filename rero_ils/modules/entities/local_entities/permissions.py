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

"""Permissions for `Local Entity` records."""
from invenio_access import action_factory

from rero_ils.modules.permissions import AllowedByAction, \
    RecordPermissionPolicy

# Actions to control local entity policies for CRUD operations
search_action = action_factory('locent-search')
read_action = action_factory('locent-read')
create_action = action_factory('locent-create')
update_action = action_factory('locent-update')
delete_action = action_factory('locent-delete')
access_action = action_factory('locent-access')


class LocalEntityPermissionPolicy(RecordPermissionPolicy):
    """Local entity Permission Policy used by the CRUD operations.

    Only search and read is allowed for all users.
    Other operations are denied far anybody.
    """

    can_search = [AllowedByAction(search_action)]
    can_read = [AllowedByAction(read_action)]
    can_create = [AllowedByAction(create_action)]
    can_update = [AllowedByAction(update_action)]
    can_delete = [AllowedByAction(delete_action)]
