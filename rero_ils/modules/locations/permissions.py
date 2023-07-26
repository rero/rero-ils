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

"""Permissions for locations."""
from invenio_access import action_factory

from rero_ils.modules.permissions import AllowedByAction, \
    AllowedByActionRestrictByManageableLibrary, \
    AllowedByActionRestrictByOrganisation, RecordPermissionPolicy

# Actions to control location policy
search_action = action_factory('loc-search')
read_action = action_factory('loc-read')
create_action = action_factory('loc-create')
update_action = action_factory('loc-update')
delete_action = action_factory('loc-delete')
access_action = action_factory('loc-access')


class LocationPermissionPolicy(RecordPermissionPolicy):
    """Location Permission Policy used by the CRUD operations."""

    can_search = [AllowedByAction(search_action)]
    can_read = [AllowedByActionRestrictByOrganisation(read_action)]
    can_create = [AllowedByActionRestrictByManageableLibrary(create_action)]
    can_update = [AllowedByActionRestrictByManageableLibrary(update_action)]
    can_delete = [AllowedByActionRestrictByManageableLibrary(delete_action)]
