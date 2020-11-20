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

"""Permissions for libraries."""

from rero_ils.modules.organisations.api import current_organisation
from rero_ils.modules.patrons.api import current_patron
from rero_ils.modules.permissions import RecordPermission


class LibraryPermission(RecordPermission):
    """Library permissions."""

    @classmethod
    def list(cls, user, record=None):
        """List permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True is action can be done.
        """
        # List libraries allowed only for staff members (lib, sys_lib)
        return current_patron and current_patron.is_librarian

    @classmethod
    def read(cls, user, record):
        """Read permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True is action can be done.
        """
        if not current_patron:
            return False
        # only staff members (lib, sys_lib) are allowed to read an library
        if not current_patron.is_librarian:
            return False
        # For staff users, they can read only own organisation libraries
        return current_organisation['pid'] == record.organisation_pid

    @classmethod
    def create(cls, user, record=None):
        """Create permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True is action can be done.
        """
        # only sys_lib user can create library
        if not current_patron or not current_patron.is_system_librarian:
            return False
        # sys_lib can only create library for its own organisation
        if record and current_organisation['pid'] != record.organisation_pid:
            return False
        return True

    @classmethod
    def update(cls, user, record):
        """Update permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True is action can be done.
        """
        # only staff members (lib, sys_lib) can update library
        # record cannot be null
        if not current_patron or not current_patron.is_librarian or not record:
            return False
        if current_organisation['pid'] == record.organisation_pid:
            # 'sys_lib' can update all libraries
            if current_patron.is_system_librarian:
                return True
            # 'lib' can only update library linked to its own library
            if current_patron.is_librarian:
                return current_patron.library_pids and \
                       record['pid'] in current_patron.library_pids
        return False

    @classmethod
    def delete(cls, user, record):
        """Delete permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True if action can be done.
        """
        if not record:
            return False
        # same as create
        return cls.create(user, record)
