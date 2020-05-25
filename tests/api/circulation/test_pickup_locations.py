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

"""Tests REST API to update loan pickup locations."""


from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import get_json, item_record_to_a_specific_loan_state, postdata

from rero_ils.modules.loans.api import LoanState


def test_update_loan_pickup_location(
        client, librarian_martigny_no_email,
        patron_martigny_no_email, loc_public_martigny, loc_public_saxon,
        item_lib_martigny, item2_lib_martigny, circulation_policies):
    """Test loan pickup location change."""
    params = {
        'patron_pid': patron_martigny_no_email.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny_no_email.pid,
        'pickup_location_pid': loc_public_saxon.pid
    }
    item, loan = item_record_to_a_specific_loan_state(
        item=item_lib_martigny, loan_state=LoanState.PENDING, params=params,
        copy_item=True)

    login_user_via_session(client, librarian_martigny_no_email.user)

    # Update pickup location of the request, no loan pid
    res, data = postdata(
        client,
        'api_item.update_loan_pickup_location',
        dict(
            item_pid=item_lib_martigny.pid,
            pickup_location_pid=loc_public_martigny.pid
        )
    )
    assert res.status_code == 400

    # Update pickup location of the request, no pickup location pid
    res, data = postdata(
        client,
        'api_item.update_loan_pickup_location',
        dict(
            item_pid=item_lib_martigny.pid,
            loan_pid=loan.pid
        )
    )
    assert res.status_code == 400

    # Update pickup location of the request
    res, data = postdata(
        client,
        'api_item.update_loan_pickup_location',
        dict(
            item_pid=item_lib_martigny.pid,
            pickup_location_pid=loc_public_martigny.pid,
            loan_pid=loan.pid
        )
    )
    assert res.status_code == 200
    assert data.get('pickup_location_pid') == loc_public_martigny.pid

    # Change loan state to 'ITEM_AT_DESK'.
    params = {
        'patron_pid': patron_martigny_no_email.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny_no_email.pid,
        'pickup_location_pid': loc_public_saxon.pid
    }
    item, loan = item_record_to_a_specific_loan_state(
        item=item2_lib_martigny,
        loan_state=LoanState.ITEM_AT_DESK, params=params,
        copy_item=True)

    # Update pickup location of the request:
    # loan state different from 'pending'
    res, data = postdata(
        client,
        'api_item.update_loan_pickup_location',
        dict(
            item_pid=item2_lib_martigny.pid,
            pickup_location_pid=loc_public_martigny.pid,
            loan_pid=loan.pid
        )
    )
    assert res.status_code == 403


def test_item_pickup_location(
        client, librarian_martigny_no_email, item2_lib_martigny):
    """Test get item pickup locations."""
    login_user_via_session(client, librarian_martigny_no_email.user)
    # test with dummy data will return 404
    res = client.get(
        url_for(
            'api_item.get_pickup_locations',
            item_pid='dummy_pid'
        )
    )
    assert res.status_code == 404
    # test with an existing item
    res = client.get(
        url_for(
            'api_item.get_pickup_locations',
            item_pid=item2_lib_martigny.pid
        )
    )
    assert res.status_code == 200
    data = get_json(res)
    assert 'locations' in data
