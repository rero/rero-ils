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

"""Test item circulation extend actions at external library."""


from rero_ils.modules.loans.api import Loan
from rero_ils.modules.loans.utils import get_circ_policy


def test_extend_on_item_on_loan_with_no_requests_external_library(
        app, item_on_loan_martigny_patron_and_loan_on_loan,
        loc_public_martigny, librarian_martigny, lib_martigny, lib_saxon,
        circulation_policies, loc_public_saxon):
    """Test extend an on_loan item at an external library."""
    item, patron, loan = item_on_loan_martigny_patron_and_loan_on_loan
    settings = app.config['CIRCULATION_POLICIES']['extension']
    app.config['CIRCULATION_POLICIES']['extension']['from_end_date'] = True
    loan['end_date'] = loan['start_date']
    initial_loan = loan.update(loan, dbcommit=True, reindex=True)
    assert get_circ_policy(
        loan, checkout_location=True) == get_circ_policy(loan)
    # The cipo used for the checkout or renewal is "short" which is configured
    # only for lib_martigny. For other libraries it is the default cipo to be
    # used.
    params = {
        'transaction_location_pid': loc_public_saxon.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    cipo = get_circ_policy(loan)
    item, actions = item.extend_loan(**params)
    loan = Loan.get_record_by_pid(initial_loan.pid)
    # now the extend action does not take into account anymore the transaction
    # library so it continues to use the "short" policy for the extend action.
    assert get_circ_policy(
        loan, checkout_location=True).get('pid') == cipo.get('pid')
    assert get_circ_policy(loan).get('pid') != cipo.get('pid')
