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

"""Permissions for ILL request."""
from rero_ils.modules.ill_requests.api import ILLRequest
from rero_ils.modules.organisations.api import current_organisation
from rero_ils.modules.patrons.api import current_patron
from rero_ils.modules.permissions import RecordPermission


class ILLRequestPermission(RecordPermission):
    """ILL request permissions."""

    @classmethod
    def list(cls, user, record=None):
        """List permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True is action can be done.
        """
        # user must be authenticated
        return bool(current_patron)

    @classmethod
    def read(cls, user, record):
        """Read permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True is action can be done.
        """
        if current_patron:
            # staff member (lib, sys_lib) can always read request from their
            # own organisation
            if current_patron.is_librarian:
                return current_organisation.pid \
                       == ILLRequest(record).organisation_pid
            # patron can only read their own requests
            if current_patron.is_patron:
                return record.patron_pid == current_patron.pid
        return False

    @classmethod
    def create(cls, user, record=None):
        """Create permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True is action can be done.
        """
        # user must be authenticated
        return bool(current_patron)

    @classmethod
    def update(cls, user, record):
        """Update permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True is action can be done.
        """
        # only staff members (lib, sys_lib) can update request
        # record cannot be null
        if not current_patron or not current_patron.is_librarian or not record:
            return False
        if current_organisation['pid'] == ILLRequest(record).organisation_pid:
            # 'sys_lib' can update all request
            if current_patron.is_system_librarian:
                return True
            # 'lib' can only update request linked to its own library
            return current_patron.library_pid and \
                record.get_library().pid == current_patron.library_pid
        return False

    @classmethod
    def delete(cls, user, record):
        """Delete permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True if action can be done.
        """
        # no one can delete an ill_request. (Use closed status instead)
        return False
