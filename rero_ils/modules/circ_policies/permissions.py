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

"""Circulation policies permissions."""

from rero_ils.modules.patrons.api import current_librarian
from rero_ils.modules.permissions import RecordPermission
from rero_ils.modules.utils import extracted_data_from_ref


class CirculationPolicyPermission(RecordPermission):
    """Circulation policy permissions."""

    @classmethod
    def list(cls, user, record=None):
        """List permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True is action can be done.
        """
        # Operation allowed only for staff members (lib, sys_lib)
        return bool(current_librarian)

    @classmethod
    def read(cls, user, record):
        """Read permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True is action can be done.
        """
        # Check the user is authenticated and a record exists as param.
        if not record or not current_librarian:
            return False
        # Check if record correspond to user owning organisation and that user
        # is (at least) a librarian
        return current_librarian.organisation_pid == record.organisation_pid

    @classmethod
    def create(cls, user, record=None):
        """Create permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True is action can be done.
        """
        # only system_librarian can create circulation policy ...
        if not current_librarian or not current_librarian.has_full_permissions:
            return False
        # ... only for its own organisation
        if record:
            return current_librarian.organisation_pid == \
                record.organisation_pid
        return True

    @classmethod
    def update(cls, user, record):
        """Update permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True is action can be done.
        """
        # User must be be authenticated and have (at least) librarian role
        if not current_librarian:
            return False
        if current_librarian and not record:  # legacy
            return True
        # * User can only update record of its own organisation
        #   - 'sys_lib' could always update a record
        #   - 'lib' could only update cipo, if :
        #     --> cipo is defined at the library level
        #     --> current user library is into the cipo libraries list
        if current_librarian.organisation_pid == record.organisation_pid:
            if current_librarian.has_full_permissions:
                return True
            # librarian
            elif record.get('policy_library_level', False):
                cipo_library_pids = []
                for library in record.get('libraries', []):
                    cipo_library_pids.append(extracted_data_from_ref(library))
                # Intersection patron libraries pid and cipo library pids
                return len(set(current_librarian.library_pids).intersection(
                    cipo_library_pids)) > 0
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
