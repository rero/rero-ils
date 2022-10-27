# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
# Copyright (C) 2019-2022 UCLouvain
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

"""Permissions for notifications."""
from invenio_access import action_factory

from rero_ils.modules.permissions import AllowedByAction, \
    AllowedByActionRestrictByManageableLibrary, \
    AllowedByActionRestrictByOwnerOrOrganisation, RecordPermissionPolicy

# Actions to control Items policies for CRUD operations
search_action = action_factory('notif-search')
read_action = action_factory('notif-read')
create_action = action_factory('notif-create')
update_action = action_factory('notif-update')
delete_action = action_factory('notif-delete')
access_action = action_factory('notif-access')


class NotificationPermissionPolicy(RecordPermissionPolicy):
    """Notification Permission Policy used by the CRUD operations."""

    # Some notifications subclasses have a library_pid, some have not.
    # in the second case, if we return `None` the permission may be
    # allowed if user has required ActionNeed, but we won't ; so return
    # a "dummy" value to always disallow the operation if a notification
    # don't have the `library_pid` property.

    can_search = [AllowedByAction(search_action)]
    can_read = [AllowedByActionRestrictByOwnerOrOrganisation(read_action)]
    can_create = [AllowedByActionRestrictByManageableLibrary(
        create_action,
        callback=lambda rec: getattr(rec, 'library_pid', 'unavailable_data')
    )]
    can_update = [AllowedByActionRestrictByManageableLibrary(
        update_action,
        callback=lambda rec: getattr(rec, 'library_pid', 'unavailable_data')
    )]
    can_delete = [AllowedByActionRestrictByManageableLibrary(
        delete_action,
        callback=lambda rec: getattr(rec, 'library_pid', 'unavailable_data')
    )]
