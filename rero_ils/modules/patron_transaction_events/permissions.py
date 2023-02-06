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

"""Permissions for Patron transaction event."""
from invenio_access import action_factory

from rero_ils.modules.permissions import AllowedByAction, \
    AllowedByActionRestrictByOrganisation, \
    AllowedByActionRestrictByOwnerOrOrganisation, RecordPermissionPolicy

# Actions to control patron transaction event policies for CRUD operations
search_action = action_factory('ptre-search')
read_action = action_factory('ptre-read')
create_action = action_factory('ptre-create')
update_action = action_factory('ptre-update')
delete_action = action_factory('ptre-delete')


class PatronTransactionEventPermissionPolicy(RecordPermissionPolicy):
    """PatronTransactionEvent permission policy used by the CRUD operations."""

    can_search = [AllowedByAction(search_action)]
    can_read = [AllowedByActionRestrictByOwnerOrOrganisation(read_action)]
    can_create = [AllowedByActionRestrictByOrganisation(create_action)]
    can_update = [AllowedByActionRestrictByOrganisation(update_action)]
    can_delete = [AllowedByActionRestrictByOrganisation(delete_action)]
