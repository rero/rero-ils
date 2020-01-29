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

"""Patron Transaction permissions."""


from .api import PatronTransaction
from ...permissions import patron_is_authenticated, staffer_is_authenticated, \
    user_is_authenticated


def can_list_patron_transaction_factory(record, *args, **kwargs):
    """Checks if the logged user have access to patron transactions list.

    only authenticated users can place a search on patron transactions.
    """
    def can(self):
        patron = user_is_authenticated()
        if patron:
            return True
        return False
    return type('Check', (), {'can': can})()


def can_read_patron_transaction_factory(record, *args, **kwargs):
    """Checks if the logged user have access to transactions of its org.

    users with librarian or system_librarian roles can acess all transactions.
    users with patron role can access only its transactions
    """
    def can(self):
        patron = staffer_is_authenticated() or patron_is_authenticated()
        if patron and patron.organisation_pid == \
                PatronTransaction(record).organisation_pid:
            if patron.is_librarian or patron.is_system_librarian:
                return True
            elif patron.is_patron and \
                    PatronTransaction(record).patron_pid == patron.pid:
                return True
        return False
    return type('Check', (), {'can': can})()
