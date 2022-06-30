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

"""Permissions for locations."""

from rero_ils.modules.patrons.api import current_librarian, current_patrons
from rero_ils.modules.permissions import RecordPermission


class LocationPermission(RecordPermission):
    """Location permissions."""

    @classmethod
    def list(cls, user, record=None):
        """List permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True is action can be done.
        """
        return bool(current_librarian or current_patrons)

    @classmethod
    def read(cls, user, record):
        """Read permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True is action can be done.
        """
        return bool(current_librarian or current_patrons)

    @classmethod
    def create(cls, user, record=None):
        """Create permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True is action can be done.
        """
        # only staff members (sys_lib, lib) can create location
        if not current_librarian:
            return False
        if not record:  # Used to to know if user could create some location
            return True
        else:
            # same as update
            return cls.update(user, record)

    @classmethod
    def update(cls, user, record):
        """Update permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True is action can be done.
        """
        # only staff members (lib, sys_lib) can update location
        # record cannot be null
        if not current_librarian or not record:
            return False
        if current_librarian.organisation_pid == record.organisation_pid:
            # 'sys_lib' can update all locations
            if current_librarian.has_full_permissions:
                return True
            # 'lib' can only update location linked to its own library
            else:
                return current_librarian.library_pids and \
                       record.library_pid in current_librarian.library_pids
        return False

    @classmethod
    def delete(cls, user, record):
        """Delete permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True if action can be done.
        """
        # same as update
        return cls.update(user, record)
