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

"""Loan permissions."""


from .api import Loan
from ...permissions import patron_is_authenticated, staffer_is_authenticated, \
    user_is_authenticated


def can_list_loan_factory(record, *args, **kwargs):
    """Checks if the logged user have access to loans list.

    only authenticated users can place a search on loans.
    """
    def can(self):
        patron = user_is_authenticated()
        if patron:
            return True
        return False
    return type('Check', (), {'can': can})()


def can_read_loan_factory(record, *args, **kwargs):
    """Checks if the logged user have access to loans of its organisation.

    users with librarian or system_librarian roles can acess all loans.
    users with patron role can access only its loans
    """
    def can(self):
        patron = staffer_is_authenticated() or patron_is_authenticated()
        if patron and patron.organisation_pid == Loan(record).organisation_pid:
            if patron.is_librarian or patron.is_system_librarian:
                return True
            elif patron.is_patron and Loan(record).patron_pid == patron.pid:
                return True
        return False
    return type('Check', (), {'can': can})()
