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

"""Tests REST return an item API methods in the item api_views."""


from invenio_accounts.testutils import login_user_via_session
from utils import get_json, postdata

from rero_ils.modules.items.api import Item
from rero_ils.modules.items.models import ItemStatus
from rero_ils.modules.loans.api import Loan, LoanAction, LoanState, \
    get_last_transaction_loc_for_item, get_loans_by_patron_pid


def test_checkin_an_item(
        client, librarian_martigny_no_email, lib_martigny,
        item_on_loan_martigny_patron_and_loan_on_loan, loc_public_martigny,
        item2_on_loan_martigny_patron_and_loan_on_loan,
        circulation_policies):
    """Test the frontend return a checked-out item action."""
    # test passes when all required parameters are given
    login_user_via_session(client, librarian_martigny_no_email.user)
    item, patron, loan = item_on_loan_martigny_patron_and_loan_on_loan

    # test fails when there is a missing required parameter
    res, data = postdata(
        client,
        'api_item.checkin',
        dict(
            item_pid=item.pid
        )
    )
    assert res.status_code == 400

    # test fails when there is a missing required parameter
    res, data = postdata(
        client,
        'api_item.checkin',
        dict(
            item_pid=item.pid,
            transaction_location_pid=loc_public_martigny.pid
        )
    )
    assert res.status_code == 400

    # test fails when there is a missing required parameter
    # when item record not found in database, api returns 404
    res, data = postdata(
        client,
        'api_item.checkin',
        dict(
            transaction_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny_no_email.pid
        )
    )
    assert res.status_code == 404

    # test passes when the transaction location pid is given
    res, data = postdata(
        client,
        'api_item.checkin',
        dict(
            item_pid=item.pid,
            transaction_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny_no_email.pid
        )
    )
    assert res.status_code == 200
    item = Item.get_record_by_pid(item.pid)
    assert item.status == ItemStatus.ON_SHELF

    # test passes when the transaction library pid is given
    item, patron, loan = item2_on_loan_martigny_patron_and_loan_on_loan
    res, data = postdata(
        client,
        'api_item.checkin',
        dict(
            item_pid=item.pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny_no_email.pid
        )
    )
    assert res.status_code == 200
    item = Item.get_record_by_pid(item.pid)
    assert item.status == ItemStatus.ON_SHELF


def test_auto_checkin_else(client, librarian_martigny_no_email,
                           patron_martigny_no_email, loc_public_martigny,
                           item_lib_martigny, json_header, lib_martigny,
                           loc_public_saxon):
    """Test item checkin no action."""
    login_user_via_session(client, librarian_martigny_no_email.user)
    res, data = postdata(
        client,
        'api_item.checkin',
        dict(
            item_pid=item_lib_martigny.pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny_no_email.pid
        )
    )
    assert res.status_code == 400
    assert get_json(res)['status'] == 'error: No circulation action performed'
