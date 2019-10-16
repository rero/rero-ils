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

"""Location permissions."""


from ...permissions import staffer_is_authenticated


def can_update_delete_location_factory(record, *args, **kwargs):
    """Checks if logged user can update or delete its organisation locations.

    user must have librarian or system_librarian role
    librarian can only update or delete its affiliated library locations.
    sys_librarian can update or delete any location of its organisation.
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


def can_create_location_factory(record, *args, **kwargs):
    """Checks if the logged user can create locations of its organisation.

    librarian can create locations for its library only.
    system_librarian can create locations at any library of its org.
    system_librarian or librarian can create locations at another org.
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
