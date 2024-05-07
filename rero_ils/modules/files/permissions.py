# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2024 RERO
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

"""Files permissions."""

from invenio_access import action_factory
from invenio_records_permissions.generators import SystemProcess

from rero_ils.modules.permissions import AllowedByAction, \
    AllowedByActionRestrictByManageableLibrary, RecordPermissionPolicy
from rero_ils.modules.utils import extracted_data_from_ref

# Actions to control Record Files policies for CRUD operations
search_action = action_factory("file-search")
read_action = action_factory("file-read")
create_action = action_factory("file-create")
update_action = action_factory("file-update")
delete_action = action_factory("file-delete")
access_action = action_factory("file-access")


def get_library_pid(record):
    """Get the library pid from the record files.

    @param record: a file record instance.
    @returns: the library pid value.
    @rtype: string.
    """
    return extracted_data_from_ref(record.get("metadata", {}).get("library"))


class FilePermissionPolicy(RecordPermissionPolicy):
    """Files permission policies."""

    # standard CRUD operation
    can_search = [AllowedByAction(search_action), SystemProcess()]
    can_read = [AllowedByAction(read_action), SystemProcess()]
    can_create = [AllowedByAction(create_action), SystemProcess()]
    can_update = [
        AllowedByActionRestrictByManageableLibrary(
            update_action, get_library_pid),
        SystemProcess(),
    ]
    can_delete = [
        AllowedByActionRestrictByManageableLibrary(
            delete_action, get_library_pid),
        SystemProcess(),
    ]
    # download/upload a file
    can_get_content_files = [AllowedByAction(read_action), SystemProcess()]
    can_set_content_files = [
        AllowedByActionRestrictByManageableLibrary(
            create_action, get_library_pid),
        SystemProcess()
    ]
    # files container
    can_read_files = [AllowedByAction(read_action), SystemProcess()]
    can_create_files = [AllowedByAction(create_action), SystemProcess()]
    can_commit_files = [
        AllowedByActionRestrictByManageableLibrary(
            create_action, get_library_pid),
        SystemProcess(),
    ]
    can_update_files = [
        AllowedByActionRestrictByManageableLibrary(
            update_action, get_library_pid),
        SystemProcess(),
    ]
    can_delete_files = [
        AllowedByActionRestrictByManageableLibrary(
            delete_action, get_library_pid),
        SystemProcess(),
    ]
