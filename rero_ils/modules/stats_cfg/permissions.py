# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2022 RERO
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

"""Permissions for statistics configuration."""

from elasticsearch_dsl.query import Q

from rero_ils.modules.patrons.api import current_librarian
from rero_ils.modules.permissions import RecordPermission
from rero_ils.permissions import admin_permission, librarian_permission


class StatCfgPermission(RecordPermission):
    """Stat configuration permissions."""

    @classmethod
    def list(cls, user, record=None):
        """List permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True is action can be done.
        """
        # list only if system librarian
        if librarian_permission.require().can():
            if current_librarian and current_librarian.is_system_librarian:
                return True
        if admin_permission.require().can():
            return True
        return False

    @classmethod
    def read(cls, user, record):
        """Read permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True is action can be done.
        """
        # read only cfgs of the current_librarian organisation
        if librarian_permission.require().can():
            if current_librarian and current_librarian.is_system_librarian:
                org_pid = current_librarian.organisation_pid
                if record['org_pid'] == org_pid:
                    return True
        if admin_permission.require().can():
            return True
        return False

    @classmethod
    def create(cls, user, record=None):
        """Create permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True is action can be done.
        """
        # create only if system librarian
        return cls.list(user)

    @classmethod
    def update(cls, user, record):
        """Update permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True is action can be done.
        """
        # update only cfgs created by current_librarian.pid
        if librarian_permission.require().can():
            if current_librarian and current_librarian.is_system_librarian:
                if record['librarian_pid'] == current_librarian.pid:
                    return True
        if admin_permission.require().can():
            return True
        return False

    @classmethod
    def delete(cls, user, record):
        """Delete permission check.

        :param user: Logged user.
        :param record: Record to check.
        :return: True if action can be done.
        """
        # delete only cfgs created by current_librarian.pid
        return cls.update(user, record)


def permission_filter():
    """Permission filter.

    Display only configurations of the current system librarian organisation.
    """
    if current_librarian and current_librarian.is_system_librarian:
        org_pid = current_librarian.organisation_pid
        return [Q('term', org_pid=org_pid)]
    return None
