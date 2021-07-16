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
from rero_ils.modules.patrons.api import current_librarian, current_patrons
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
        return bool(current_patrons or current_librarian)

    @classmethod
    def read(cls, user, record):
        """Read permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True is action can be done.
        """
        if current_librarian:
            # staff member (lib, sys_lib) can always read request from their
            # own organisation
            return current_librarian.organisation_pid \
                    == ILLRequest(record).organisation_pid
        # patron can only read their own requests
        elif current_patrons:
            return record.patron_pid in [ptrn.pid for ptrn in current_patrons]
        return False

    @classmethod
    def create(cls, user, record=None):
        """Create permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True is action can be done.
        """
        # user must be authenticated
        return bool(current_librarian or current_patrons)

    @classmethod
    def update(cls, user, record):
        """Update permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True is action can be done.
        """
        # only staff members (lib, sys_lib) can update request
        # record cannot be null
        if not current_librarian or not record:
            return False
        return current_librarian.organisation_pid == \
            ILLRequest(record).organisation_pid

    @classmethod
    def delete(cls, user, record):
        """Delete permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True if action can be done.
        """
        # no one can delete an ill_request. (Use closed status instead)
        return False
