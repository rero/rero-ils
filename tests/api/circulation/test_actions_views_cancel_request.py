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

"""Tests REST cancel item request API methods in the item api_views."""


from invenio_accounts.testutils import login_user_via_session
from utils import postdata

from rero_ils.modules.loans.api import Loan, LoanAction, LoanState, \
    get_last_transaction_loc_for_item, get_loans_by_patron_pid


def test_cancel_an_item_request(
        client, librarian_martigny_no_email, lib_martigny,
        item_at_desk_martigny_patron_and_loan_at_desk,
        item_on_shelf_martigny_patron_and_loan_pending, loc_public_martigny,
        circulation_policies):
    """Test the frontend cancel an item request action."""
    # test passes when all required parameters are given
    login_user_via_session(client, librarian_martigny_no_email.user)
    item, patron, loan = item_on_shelf_martigny_patron_and_loan_pending

    # test fails when there is a missing required parameter
    res, data = postdata(
        client,
        'api_item.cancel_item_request',
        dict(
            pid=loan.pid
        )
    )
    assert res.status_code == 400

    # test fails when there is a missing required parameter
    res, data = postdata(
        client,
        'api_item.cancel_item_request',
        dict(
            pid=loan.pid,
            transaction_location_pid=loc_public_martigny.pid
        )
    )
    assert res.status_code == 400

    # test fails when there is a missing required parameter
    # when item record not found in database, api returns 404
    res, data = postdata(
        client,
        'api_item.cancel_item_request',
        dict(
            transaction_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny_no_email.pid
        )
    )
    assert res.status_code == 404

    # test passes when the transaction location pid is given
    res, data = postdata(
        client,
        'api_item.cancel_item_request',
        dict(
            pid=loan.pid,
            transaction_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny_no_email.pid
        )
    )
    assert res.status_code == 200

    # test passes when the transaction library pid is given
    login_user_via_session(client, librarian_martigny_no_email.user)
    item, patron, loan = item_at_desk_martigny_patron_and_loan_at_desk
    res, data = postdata(
        client,
        'api_item.cancel_item_request',
        dict(
            pid=loan.pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny_no_email.pid
        )
    )
    assert res.status_code == 200
