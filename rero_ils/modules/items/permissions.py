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

"""Item permissions."""


from ...permissions import staffer_is_authenticated


def can_update_delete_item_factory(record, *args, **kwargs):
    """Checks if logged user can update or delete its organisation items.

    librarian must have librarian or system_librarian role.
    librarian can only update, delete items of its affiliated library.
    sys_librarian can update, delete any item of its org only.
    """
    def can(self):
        patron = staffer_is_authenticated()
        if patron and patron.organisation_pid == record.organisation_pid:
            return check_patron_library_permissions(patron, record)
        return False
    return type('Check', (), {'can': can})()


def can_create_item_factory(record, *args, **kwargs):
    """Checks if the logged user can create items for its organisation.

    librarian must have librarian or system_librarian role.
    librarian can only create items in its affiliated library.
    sys_librarian can create any item of its org only.
    """
    def can(self):
        patron = staffer_is_authenticated()
        if patron and not record:
            return True
        if patron and patron.organisation_pid == record.organisation_pid:
            return check_patron_library_permissions(patron, record)
        return False
    return type('Check', (), {'can': can})()


def check_patron_library_permissions(patron, record):
    """Checks if the logged user can create items for its organisation.

    librarian must have librarian or system_librarian role.
    librarian can only create, update, delete items in its affiliated library.
    sys_librarian can create, update, delete any item of its org only.
    """
    if not patron.is_system_librarian:
        if patron.library_pid and \
                record.library_pid != patron.library_pid:
            return False
    return True
