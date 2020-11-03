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

from rero_ils.modules.organisations.api import current_organisation
from rero_ils.modules.permissions import RecordPermission

from .api import Patron, current_patron


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
        return current_patron and current_patron.is_librarian

    @classmethod
    def read(cls, user, record):
        """Read permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True is action can be done.
        """
        # user should be authenticated
        if not current_patron:
            return False
        # only staff members (lib, sys_lib) are allowed to read an organisation
        if not current_patron.is_librarian:
            return False
        # For staff users, they can read only their own organisation.
        return current_organisation['pid'] == record.organisation_pid

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
        if not current_patron or not current_patron.is_librarian:
            return False
        # ... only for its own organisation
        if record:
            if current_organisation['pid'] == record.organisation_pid:
                # sys_lib can manage all kind of patron
                if current_patron.is_system_librarian:
                    return True
                # librarian user has some restrictions...
                if current_patron.is_librarian:
                    # a librarian cannot manage a system_librarian patron
                    if 'system_librarian' in incoming_record.get('roles', [])\
                       or 'system_librarian' in record.get('roles', []):
                        return False
                    # a librarian can only manage other librarian from its own
                    # library
                    if current_patron.library_pid and record.library_pid and\
                       record.library_pid != current_patron.library_pid:
                        return False
                    return True
            return False
        return True

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
        if current_patron and record.pid == current_patron.pid:
            return False
        return cls.create(user, record)


def get_allowed_roles_management():
    """Get the roles that current logged user could manage.

    :return An array of allowed role management.
    """
    allowed_roles = []
    if current_patron and current_patron.is_librarian:
        if current_patron.is_librarian:
            allowed_roles.append(Patron.ROLE_PATRON)
            allowed_roles.append(Patron.ROLE_LIBRARIAN)
        if current_patron.is_system_librarian:
            allowed_roles.append(Patron.ROLE_SYSTEM_LIBRARIAN)
    return allowed_roles
