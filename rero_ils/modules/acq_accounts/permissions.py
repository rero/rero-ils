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

"""AcqAccount permissions."""

from ...permissions import staffer_is_authenticated


def can_read_update_delete_acq_account_factory(record, *args, **kwargs):
    """Checks if logged user can update or delete its organisation accounts.

    user must have librarian or system_librarian role
    librarian can only update or delete its affiliated library accounts.
    sys_librarian can update or delete any account of its organisation.
    """
    def can(self):
        patron = staffer_is_authenticated()
        if patron and patron.organisation_pid == record.organisation_pid:
            if not patron.is_system_librarian:
                if patron.library_pid and \
                        record.library_pid != patron.library_pid:
                    return False
            return True
        return False
    return type('Check', (), {'can': can})()


def can_create_acq_account_factory(record, *args, **kwargs):
    """Checks if the logged user can create accounts of its organisation.

    librarian can create accounts for its library only.
    system_librarian can create accounts at any library of its org.
    system_librarian or librarian can not create accounts at another org.
    """
    def can(self):
        patron = staffer_is_authenticated()
        if patron and not record:
            return True
        if patron and patron.organisation_pid == record.organisation_pid:
            if patron.is_system_librarian:
                return True
            if patron.is_librarian and \
                    record.library_pid == patron.library_pid:
                return True
        return False
    return type('Check', (), {'can': can})()


def can_list_acq_account_factory(record, *args, **kwargs):
    """Checks if the logged user have access to accounts list.

    only authenticated users can place a search on accounts.
    """
    def can(self):
        patron = staffer_is_authenticated()
        if patron:
            return True
        return False
    return type('Check', (), {'can': can})()
