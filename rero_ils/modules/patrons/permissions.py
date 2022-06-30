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

"""Permissions for patrons."""
from flask import request

from rero_ils.modules.permissions import RecordPermission
from rero_ils.modules.users.models import UserRole

from .api import current_librarian


class PatronPermission(RecordPermission):
    """Patrons permissions."""

    @classmethod
    def list(cls, user, record=None):
        """List permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True is action can be done.
        """
        # All staff members (lib, sys_lib) can list patrons
        return bool(current_librarian)

    @classmethod
    def read(cls, user, record):
        """Read permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True is action can be done.
        """
        # For staff users, they can read only their own organisation.
        return current_librarian and \
            current_librarian.organisation_pid == record.organisation_pid

    @classmethod
    def create(cls, user, record=None):
        """Create permission check.

        :param user: Logged user.
        :param record: pre-existing Record to check.
        :return: True is action can be done.
        """
        incoming_record = request.get_json(silent=True) or {}
        return cls.can_create(user, record, incoming_record)

    @classmethod
    def can_create(cls, user, record, incoming_record):
        """Create permission check.

        :param user: Logged user.
        :param record: pre-existing Record to check.
        :param record: new incoming Record data.
        :return: True is action can be done.
        """
        # only staff members (lib, sys_lib) can create patrons ...
        # ... only for its own organisation
        if current_librarian:
            # can create a record
            if not record:
                return True
            if current_librarian.organisation_pid == record.organisation_pid:
                # sys_lib can manage all kind of patron
                if current_librarian.has_full_permissions:
                    return True
                # librarian user has some restrictions...
                # a librarian cannot manage a system_librarian patron
                if UserRole.FULL_PERMISSIONS in \
                   incoming_record.get('roles', []) \
                   or UserRole.FULL_PERMISSIONS in record.get('roles', []):
                    return False
                # a librarian can only manage other librarian from its own
                # library
                if record.library_pid and \
                        record.library_pid not in \
                        current_librarian.library_pids:
                    return False
                return True
        return False

    @classmethod
    def update(cls, user, record):
        """Update permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True is action can be done.
        """
        if not record:
            return False
        return cls.create(user, record)

    @classmethod
    def delete(cls, user, record):
        """Delete permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True if action can be done.
        """
        if not record:
            return False
        # It should be not possible to remove itself
        if current_librarian and record.pid == current_librarian.pid:
            return False
        return cls.create(user, record)


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
