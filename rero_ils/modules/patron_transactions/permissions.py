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

"""Permissions for Patron transaction."""

from rero_ils.modules.patrons.api import current_librarian, current_patrons
from rero_ils.modules.permissions import RecordPermission


class PatronTransactionPermission(RecordPermission):
    """Patron transaction permissions."""

    @classmethod
    def list(cls, user, record=None):
        """List permission check.

        :param user: Logged user.
        :param record: Record to check
        :return: True is action can be done.
        """
        # user should be authenticated
        return bool(current_patrons or current_librarian)

    @classmethod
    def read(cls, user, record):
        """Read permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True is action can be done.
        """
        #  For staff users (lib, sys_lib), they can read only their own
        #  organisation.
        if current_librarian and \
                current_librarian.organisation_pid == record.organisation_pid:
            return True
        # For other people (patron), they can read only their own transaction
        return record and \
            record.patron_pid in [ptrn.pid for ptrn in current_patrons]

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
        if not record:
            return False
        return current_librarian and \
            current_librarian.organisation_pid == record.organisation_pid

    @classmethod
    def delete(cls, user, record):
        """Delete permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True if action can be done.
        """
        # Same as update
        return cls.update(user, record)
