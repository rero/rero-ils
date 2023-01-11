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

"""Permissions for patrons."""
from flask import g
from flask_login import current_user
from invenio_access import action_factory, any_user
from invenio_records_permissions.generators import Generator

from rero_ils.modules.permissions import AllowedByAction, \
    AllowedByActionRestrictByOrganisation, \
    AllowedByActionRestrictByOwnerOrOrganisation, LibraryNeed, \
    RecordPermissionPolicy
from rero_ils.modules.users.models import UserRole

from .api import Patron, current_librarian
from .utils import validate_role_changes

# Actions to control patron permission policy
search_action = action_factory('ptrn-search')
read_action = action_factory('ptrn-read')
create_action = action_factory('ptrn-create')
update_action = action_factory('ptrn-update')
delete_action = action_factory('ptrn-delete')
access_action = action_factory('ptrn-access')


class AllowedByActionRestrictStaffByManageableLibrary(
      AllowedByActionRestrictByOrganisation):
    """Restrict action on staff users by staff users of the same library.

    If the updated record represents a staff `Patron` user, then only staff
    members related to the same library that this record could update it.
    """

    def needs(self, record=None, *args, **kwargs):
        """Allows the given action depending on record.

        :param record: the record to check.
        :param args: extra arguments.
        :param kwargs: extra named arguments.
        :returns: a list of Needs to validate access.
        """
        if not isinstance(record, Patron):
            record = Patron(record)

        record_roles = record.get('roles', [])
        # If updated user is a staff member, only user related to the same
        # library (so only staff members because simple patron are not
        # related to any library) can perform operation on this user.
        if set(UserRole.PROFESSIONAL_ROLES).intersection(record_roles):
            required_needs = [LibraryNeed(pid) for pid in record.library_pids]
            if not g.identity.provides.intersection(required_needs):
                return []
        return super().needs(record, *args, **kwargs)


class RestrictDeleteDependOnPatronRolesManagement(Generator):
    """Restrict deletion of patron depending on role management restrictions.

    Depending on the current logged user profile, some roles' management
    updates could be disallowed. Manageable roles are defined into the
    `RERO_ILS_PATRON_ROLES_MANAGEMENT_RESTRICTIONS` configuration attribute.
    """

    def excludes(self, record=None, **kwargs):
        """Disallow operation check.

        :param record; the record to check.
        :param kwargs: extra named arguments.
        :returns: a list of Needs to disable access.
        """
        roles = set(record.get('roles', []))
        if not validate_role_changes(current_user, roles, raise_exc=False):
            return [any_user]
        return []


class PatronPermissionPolicy(RecordPermissionPolicy):
    """Patron Permission Policy used by the CRUD operations."""

    can_search = [AllowedByAction(search_action)]
    can_read = [AllowedByActionRestrictByOwnerOrOrganisation(
        read_action,
        patron_callback=lambda record: record.pid
    )]
    can_create = [
        AllowedByActionRestrictStaffByManageableLibrary(create_action)
    ]
    can_update = [
        AllowedByActionRestrictStaffByManageableLibrary(update_action)
    ]
    can_delete = [
        AllowedByActionRestrictStaffByManageableLibrary(delete_action),
        RestrictDeleteDependOnPatronRolesManagement()
    ]


def get_allowed_roles_management():
    """Get the roles that current logged user could manage.

    :return An array of allowed role management.
    """
    allowed_roles = []
    if current_librarian:
        allowed_roles += [UserRole.PATRON] + UserRole.LIBRARIAN_ROLES
        if current_librarian.has_full_permissions:
            allowed_roles += [UserRole.FULL_PERMISSIONS]
    return allowed_roles
