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

"""Tests REST change pickup location API methods in the item api_views."""


from invenio_accounts.testutils import login_user_via_session
from utils import postdata

from rero_ils.modules.loans.api import Loan, LoanAction, LoanState, \
    get_last_transaction_loc_for_item, get_loans_by_patron_pid


def test_change_pickup_location_request(
        client, librarian_martigny_no_email, lib_martigny,
        item_at_desk_martigny_patron_and_loan_at_desk,
        item_on_shelf_martigny_patron_and_loan_pending, loc_public_martigny,
        circulation_policies, loc_public_fully):
    """Test the frontend update pickup location calls."""
    login_user_via_session(client, librarian_martigny_no_email.user)
    item, patron, loan = item_on_shelf_martigny_patron_and_loan_pending

    # test fails when there is a missing required parameter
    res, data = postdata(
        client,
        'api_item.update_loan_pickup_location',
        dict(
            pid=loan.pid
        )
    )
    assert res.status_code == 400

    # test fails when there is a missing required parameter
    res, data = postdata(
        client,
        'api_item.update_loan_pickup_location',
        dict(
            pickup_location_pid=loc_public_martigny.pid
        )
    )
    assert res.status_code == 400

    # test passes all required parameters are given
    # CHANGE_PICKUP_LOCATION_1_2: update is allowed on PENDING loans.
    res, data = postdata(
        client,
        'api_item.update_loan_pickup_location',
        dict(
            pid=loan.pid,
            pickup_location_pid=loc_public_fully.pid
        )
    )
    assert res.status_code == 200


def test_change_pickup_location_request_for_other_loans(
        client, librarian_martigny_no_email, lib_martigny,
        item_at_desk_martigny_patron_and_loan_at_desk,
        loc_public_martigny, circulation_policies, loc_public_fully,
        item_on_loan_martigny_patron_and_loan_on_loan,
        item_in_transit_martigny_patron_and_loan_for_pickup,
        item_in_transit_martigny_patron_and_loan_to_house):
    """Test the frontend update pickup location calls of other loan states."""
    login_user_via_session(client, librarian_martigny_no_email.user)
    # CHANGE_PICKUP_LOCATION_2_1: update denied on ITEM_ON_LOAN loans.
    item, patron, loan = item_at_desk_martigny_patron_and_loan_at_desk
    res, data = postdata(
        client,
        'api_item.update_loan_pickup_location',
        dict(
            pid=loan.pid,
            pickup_location_pid=loc_public_fully.pid
        )
    )
    assert res.status_code == 403
    # CHANGE_PICKUP_LOCATION_3_1: update denied on ITEM_AT_DESK loans.
    item, patron, loan = item_on_loan_martigny_patron_and_loan_on_loan
    res, data = postdata(
        client,
        'api_item.update_loan_pickup_location',
        dict(
            pid=loan.pid,
            pickup_location_pid=loc_public_fully.pid
        )
    )
    assert res.status_code == 403
    # CHANGE_PICKUP_LOCATION_4: update denied on IN_TRANSIT_FOR_PICKUP loans.
    item, patron, loan = item_in_transit_martigny_patron_and_loan_for_pickup
    res, data = postdata(
        client,
        'api_item.update_loan_pickup_location',
        dict(
            pid=loan.pid,
            pickup_location_pid=loc_public_fully.pid
        )
    )
    assert res.status_code == 403
    # CHANGE_PICKUP_LOCATION_5: update is allowed on IN_TRANSIT_TO_HOUSE loans.
    item, patron, loan = item_in_transit_martigny_patron_and_loan_to_house
    res, data = postdata(
        client,
        'api_item.update_loan_pickup_location',
        dict(
            pid=loan.pid,
            pickup_location_pid=loc_public_fully.pid
        )
    )
    assert res.status_code == 200
