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

"""Permissions for patron types."""

from invenio_access import action_factory

from rero_ils.modules.permissions import AllowedByAction, \
    LibrarianWithTheSameOrganisation, RecordPermissionPolicy

ptty_read = action_factory('ptty-read')
ptty_write = action_factory('ptty-write')


class PatronTypePermissionPolicy(RecordPermissionPolicy):
    """Patron Type Permission Policy.

    Used by the CRUD operations.
    """

    can_search = [AllowedByAction('ptty-read')]
    can_read = [LibrarianWithTheSameOrganisation('ptty-read')]
    can_create = [LibrarianWithTheSameOrganisation('ptty-write')]
    can_update = [LibrarianWithTheSameOrganisation('ptty-write')]
    can_delete = [LibrarianWithTheSameOrganisation('ptty-write')]
