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

"""Loan Record API tests."""

from __future__ import absolute_import, print_function

from invenio_accounts.testutils import login_user_via_session
from utils import postdata

from rero_ils.modules.loans.api import LoanAction, patron_profile


def test_patron_profile_loans(
        client, librarian_martigny_no_email,
        patron_martigny_no_email, loc_public_martigny,
        item_lib_martigny, json_header, circulation_policies):
    """Test patron profile loans sent to patron account."""

    # No patron history
    assert not patron_profile(patron_martigny_no_email)[3]

    login_user_via_session(client, librarian_martigny_no_email.user)
    res, data = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item_lib_martigny.pid,
            patron_pid=patron_martigny_no_email.pid,
            transaction_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny_no_email.pid
        )
    )
    assert res.status_code == 200
    actions = data.get('action_applied')
    loan_pid = actions[LoanAction.CHECKOUT].get('pid')

    res, data = postdata(
        client,
        'api_item.checkin',
        dict(
            item_pid=item_lib_martigny.pid,
            pid=loan_pid,
            transaction_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny_no_email.pid
        )
    )
    assert res.status_code == 200

    # Some history are created
    assert patron_profile(patron_martigny_no_email)[3][0]['pid'] == loan_pid

    # no history is returned for deleted items.
    item_lib_martigny.delete(dbcommit=True, delindex=True)
    assert not patron_profile(patron_martigny_no_email)[3]
