# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2020 RERO
# Copyright (C) 2020 UCLouvain
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

"""Permissions for libraries."""
from invenio_access import action_factory

from rero_ils.modules.permissions import AllowedByAction, \
    AllowedByActionRestrictByManageableLibrary, \
    AllowedByActionRestrictByOrganisation, RecordPermissionPolicy

# Actions to control library policy
search_action = action_factory('lib-search')
read_action = action_factory('lib-read')
create_action = action_factory('lib-create')
update_action = action_factory('lib-update')
delete_action = action_factory('lib-delete')


class LibraryPermissionPolicy(RecordPermissionPolicy):
    """Library Permission Policy used by the CRUD operations."""

    can_search = [AllowedByAction(search_action)]
    can_read = [AllowedByActionRestrictByOrganisation(read_action)]
    can_create = [AllowedByActionRestrictByManageableLibrary(
        create_action, lambda record: record.get('pid'))]
    can_update = [AllowedByActionRestrictByManageableLibrary(
        create_action, lambda record: record.get('pid'))]
    can_delete = [AllowedByActionRestrictByManageableLibrary(
        create_action, lambda record: record.get('pid'))]
