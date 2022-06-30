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

"""Templates permissions."""

from flask import request

from rero_ils.modules.patrons.api import current_librarian
from rero_ils.modules.permissions import RecordPermission


class TemplatePermission(RecordPermission):
    """Template permissions."""

    @classmethod
    def list(cls, user, record=None):
        """List permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True if action can be done.
        """
        # Operation allowed only for staff members (lib, sys_lib)
        return bool(current_librarian)

    @classmethod
    def read(cls, user, record):
        """Read permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True if action can be done.
        """
        # Check the user is authenticated and a record exists as param.
        if not record or not current_librarian:
            return False
        # only librarian or system_librarian can read templates of own org
        if current_librarian.organisation_pid == record.organisation_pid:
            #   - 'sys_librarian' could always read any record
            if current_librarian.has_full_permissions:
                return True
            #   - 'librarian' could only read his public and his own records.
            else:
                return record.is_public or \
                    record.creator_pid == current_librarian.pid
        return False

    @classmethod
    def create(cls, user, record=None):
        """Create permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True if action can be done.
        """
        # only librarian or system_librarian can create templates
        if not current_librarian:
            return False
        if not record:
            return True
        # Same as update
        return cls.update(user, record)

    @classmethod
    def update(cls, user, record):
        """Update permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True if action can be done.
        """
        # User must be authenticated and have (at least) librarian role
        if not current_librarian:
            return False
        # User can only update record of its own organisation
        if current_librarian.organisation_pid == record.organisation_pid:
            #   - 'sys_librarian' can update public and his own private records
            if current_librarian.has_full_permissions:
                if record.is_private and \
                        record.creator_pid != current_librarian.pid:
                    return False
                return True
            #   - 'librarian' can only update his own private records
            #     He cannot change the visibility
            else:
                incoming_record = request.get_json(silent=True) or {}
                # a librarian cannot change visibility of a template
                if incoming_record and incoming_record.get('visibility') \
                   != record.get('visibility'):
                    return False
                # a librarian can update its own private record
                elif record.is_private and \
                        record.creator_pid == current_librarian.pid:
                    return True
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
        # same as update
        return cls.update(user, record)
