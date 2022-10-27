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

"""Permissions for Acquisition invoice."""

from invenio_access import action_factory

from rero_ils.modules.permissions import AllowedByAction, \
    AllowedByActionRestrictByManageableLibrary, DisallowedIfRollovered, \
    RecordPermissionPolicy

from .api import AcquisitionInvoice

# Actions to control acquisition invoices resource policies
search_action = action_factory('acin-search')
read_action = action_factory('acin-read')
create_action = action_factory('acin-create')
update_action = action_factory('acin-update')
delete_action = action_factory('acin-delete')
access_action = action_factory('acin-access')


class AcqInvoicePermissionPolicy(RecordPermissionPolicy):
    """Acquisition invoice Permission Policy used by the CRUD operations."""

    can_search = [AllowedByAction(search_action)]
    can_read = [AllowedByActionRestrictByManageableLibrary(read_action)]
    can_create = [
        AllowedByActionRestrictByManageableLibrary(create_action),
        DisallowedIfRollovered(AcquisitionInvoice)
    ]
    can_update = [
        AllowedByActionRestrictByManageableLibrary(update_action),
        DisallowedIfRollovered(AcquisitionInvoice)
    ]
    can_delete = [
        AllowedByActionRestrictByManageableLibrary(delete_action),
        DisallowedIfRollovered(AcquisitionInvoice)
    ]
