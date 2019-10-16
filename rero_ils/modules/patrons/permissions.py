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

"""Patron permissions."""

from flask import request

from ...permissions import staffer_is_authenticated


def can_update_patron_factory(record, *args, **kwargs):
    """Checks if the logged user can update its organisations patrons.

    user must have librarian or system_librarian role
    returns False if a librarian tries to update a system_librarian
    returns False if a librarian tries to add the system_librarian role.
    """
    def can(self):
        incoming_record = request.get_json(silent=True) or {}
        patron = staffer_is_authenticated()
        if patron and patron.organisation_pid == record.organisation_pid:
            if not patron.is_system_librarian:
                if (
                        'system_librarian' in incoming_record.get(
                            'roles', []) or
                        'system_librarian' in record.get('roles', [])
                ):
                    return False
                if patron.library_pid and \
                        record.library_pid and \
                        record.library_pid != patron.library_pid:
                    return False
            return True
        return False
    return type('Check', (), {'can': can})()


def can_delete_patron_factory(record, *args, **kwargs):
    """Checks if the logged user can delete records of its organisation.

    user must have librarian or system_librarian role
    returns False if a librarian tries to delete a system_librarian and if
    librarian tries to delete a librarian from another library.
    """
    def can(self):
        patron = staffer_is_authenticated()
        if patron and patron.organisation_pid == record.organisation_pid:
            if patron.is_system_librarian:
                return True
            if patron.is_librarian:
                if 'system_librarian' in record.get('roles', []):
                    return False
                if patron.library_pid and \
                        record.library_pid and \
                        record.library_pid != patron.library_pid:
                    return False
                return True
        return False
    return type('Check', (), {'can': can})()
