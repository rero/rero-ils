# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
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

"""Permissions of Operation log."""

from rero_ils.modules.patrons.api import current_patron
from rero_ils.modules.permissions import RecordPermission


class OperationLogPermission(RecordPermission):
    """Operation logs permissions."""

    @classmethod
    def list(cls, user, record=None):
        """List permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: "True" if action can be done.
        """
        # all users may list operation_log records.
        # TODO: check with group PO here.
        if not current_patron:
            return False
        return True

    @classmethod
    def read(cls, user, record):
        """Read permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: "True" if action can be done.
        """
        # all users may read operation_log records.
        # TODO: check with group PO here.
        if not current_patron:
            return False
        return True

    @classmethod
    def create(cls, user, record=None):
        """Create permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: "True" if action can be done.
        """
        # all users may create operation_log records.
        # TODO: check with group PO here.
        if not current_patron:
            return False
        return True

    @classmethod
    def update(cls, user, record):
        """Update permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: "True" if action can be done.
        """
        # operation log updates is not allowed
        return False

    @classmethod
    def delete(cls, user, record):
        """Delete permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: "True" if action can be done.
        """
        if not record:
            return False
        # delete log updates is not allowed
        return False
