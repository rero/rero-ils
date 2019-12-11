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

"""Budget permissions."""

from ...permissions import staffer_is_authenticated


def can_update_delete_budgets_factory(record, *args, **kwargs):
    """Checks if logged user can update or delete its organisation budgets.

    user must have librarian or system_librarian role
    librarian can not update nor delete its affiliated library budgets.
    sys_librarian can update or delete any budgets of its organisation.
    """
    def can(self):
        patron = staffer_is_authenticated()
        if patron and patron.organisation_pid == record.organisation_pid:
            if not patron.is_system_librarian:
                return False
            return True
        return False
    return type('Check', (), {'can': can})()


def can_create_budgets_factory(record, *args, **kwargs):
    """Checks if the logged user can create budgets of its organisation.

    librarian may not create budgets for its organisation.
    system_librarian can create budgets of its org.
    system_librarian or librarian can not create budgets at another org.
    """
    def can(self):
        if record is None:
            return True
        patron = staffer_is_authenticated()
        if patron and patron.organisation_pid == record.organisation_pid:
            if patron.is_system_librarian:
                return True
        return False
    return type('Check', (), {'can': can})()


def can_list_budgets_factory(record, *args, **kwargs):
    """Checks if the logged user have access to budget list.

    only authenticated users can place a search on budgets.
    """
    def can(self):
        patron = staffer_is_authenticated()
        if patron:
            return True
        return False
    return type('Check', (), {'can': can})()
