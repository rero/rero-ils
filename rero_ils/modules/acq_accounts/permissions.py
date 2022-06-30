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

"""Permissions for Acquisition account."""

from rero_ils.modules.patrons.api import current_librarian
from rero_ils.modules.permissions import RecordPermission


class AcqAccountPermission(RecordPermission):
    """Acquisition account permissions."""

    @classmethod
    def list(cls, user, record=None):
        """List permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True is action can be done.
        """
        # List organisation allowed only for staff members (lib, sys_lib)
        return bool(current_librarian)

    @classmethod
    def read(cls, user, record):
        """Read permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True is action can be done.
        """
        # user should be authenticated
        if not current_librarian:
            return False
        # 'lib' can only update account linked to its own library
        if current_librarian.has_full_permissions:
            return current_librarian.organisation_pid == \
                record.organisation_pid
        else:
            return current_librarian.library_pids and \
                record.library_pid in current_librarian.library_pids

    @classmethod
    def create(cls, user, record=None):
        """Create permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True is action can be done.
        """
        # user should be authenticated
        if not current_librarian:
            return False
        if not record:
            return True
        else:
            # Same as update
            return cls.update(user, record)

    @classmethod
    def update(cls, user, record):
        """Update permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True is action can be done.
        """
        # only staff members (lib, sys_lib) can update acq_account
        # record cannot be null
        if not current_librarian or not record:
            return False
        # 'sys_lib' can update all account
        if current_librarian.has_full_permissions:
            return current_librarian.organisation_pid == \
                record.organisation_pid
        # 'lib' can only update account linked to its own library
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
        # Same as update
        return cls.update(user, record)
