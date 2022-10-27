# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
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

"""Permissions of Operation log."""
from invenio_access import action_factory

from rero_ils.modules.permissions import AllowedByAction, \
    RecordPermissionPolicy

# Actions to control operation logs policies for CRUD operations
search_action = action_factory('oplg-search')
read_action = action_factory('oplg-read')
access_action = action_factory('oplg-access')


class OperationLogPermissionPolicy(RecordPermissionPolicy):
    """Operation log Permission Policy used by the CRUD operations."""

    can_search = [AllowedByAction(search_action)]
    can_read = [AllowedByAction(read_action)]
