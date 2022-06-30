# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
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

"""Permissions for organisations."""

from rero_ils.modules.patrons.api import current_librarian
from rero_ils.modules.permissions import RecordPermission


class OrganisationPermission(RecordPermission):
    """Organisations permissions."""

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
        # only staff members (lib, sys_lib) are allowed to read an organisation
        if not current_librarian:
            return False
        # For staff users, they can read only their own organisation.
        return current_librarian.organisation_pid == record['pid']

    @classmethod
    def create(cls, user, record=None):
        """Create permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True is action can be done.
        """
        # Nobody can create an organisation. To create a new organisation, use
        # the CLI interface
        return False

    @classmethod
    def update(cls, user, record):
        """Update permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True is action can be done.
        """
        # user should be authenticated
        if not current_librarian:
            return False
        # only 'system_librarian' user allowed to update their own organisation
        if not current_librarian.has_full_permissions:
            return False
        return current_librarian.organisation_pid == record['pid']

    @classmethod
    def delete(cls, user, record):
        """Delete permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True if action can be done.
        """
        # Nobody can remove an organisation
        return False
