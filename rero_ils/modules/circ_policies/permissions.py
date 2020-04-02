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

"""Circulation policies permissions."""

from ...permissions import staffer_is_authenticated, user_has_roles


def can_update_circ_policy_factory(record, *args, **kwargs):
    """Check if a user can update a circulation policy."""
    def can(self):
        patron = staffer_is_authenticated()
        if patron and not record:
            return True
        if patron and patron.organisation_pid == record.organisation_pid:
            if user_has_roles(roles=['system_librarian']):
                return True
            elif user_has_roles(roles=['librarian']) \
                    and record.get('policy_library_level', False):
                cipo_library_pids = record.replace_refs().get('libraries', [])
                cipo_library_pids = [lib['pid'] for lib in cipo_library_pids]
                return patron.library_pid in cipo_library_pids
        return False
    return type('Check', (), {'can': can})()
