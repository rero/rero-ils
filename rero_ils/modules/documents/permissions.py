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

"""Permissions for documents."""

from invenio_access import action_factory
from invenio_access.permissions import any_user
from invenio_records_permissions.generators import Generator

from rero_ils.modules.permissions import AllowedByAction, \
    RecordPermissionPolicy

# Actions to control Documents policies for CRUD operations
search_action = action_factory('doc-search')
read_action = action_factory('doc-read')
create_action = action_factory('doc-create')
update_action = action_factory('doc-update')
delete_action = action_factory('doc-delete')
access_action = action_factory('doc-access')


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
