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

"""Tests items in-transit."""


from invenio_accounts.testutils import login_user_via_session
from utils import postdata

from rero_ils.modules.items.api import Item
from rero_ils.modules.items.models import ItemStatus
from rero_ils.modules.loans.api import Loan, LoanAction


def test_items_in_transit_between_libraries(
        client, librarian_martigny_no_email, librarian_saxon_no_email,
        patron_martigny_no_email, loc_public_martigny,
        item_type_standard_martigny, loc_public_saxon, item_lib_martigny,
        json_header, circulation_policies):
    """Test item in-transit scenarios."""
    login_user_via_session(client, librarian_martigny_no_email.user)
    # checkout the item at location A
    res, data = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item_lib_martigny.pid,
            patron_pid=patron_martigny_no_email.pid,
            transaction_location_pid=loc_public_saxon.pid
        )
    )
    assert res.status_code == 200
    assert Item.get_record_by_pid(item_lib_martigny.pid).get('status') \
        == ItemStatus.ON_LOAN
    item_data = data.get('metadata')
    actions = data.get('action_applied')
    assert item_data.get('status') == ItemStatus.ON_LOAN
    loan_pid = actions[LoanAction.CHECKOUT].get('pid')

    # checkin the item at location B
    res, data = postdata(
        client,
        'api_item.checkin',
        dict(
            item_pid=item_lib_martigny.pid,
            pid=loan_pid,
            transaction_location_pid=loc_public_martigny.pid
        )
    )
    assert res.status_code == 200
    item_data = data.get('metadata')
    item = Item.get_record_by_pid(item_data.get('pid'))
    assert item.get('status') == ItemStatus.ON_SHELF


def test_item_multiple_transit(client, item_lib_martigny,
                               librarian_martigny_no_email,
                               patron_martigny_no_email, loc_public_martigny,
                               loc_public_saxon, loc_public_fully,
                               circulation_policies,
                               patron2_martigny_no_email,
                               librarian2_martigny_data):
    """Test item in-transit in different locations."""
    login_user_via_session(client, librarian_martigny_no_email.user)

    # request same item to another user to pick up at fully
    res, data = postdata(
        client,
        'api_item.librarian_request',
        dict(
            item_pid=item_lib_martigny.pid,
            pickup_location_pid=loc_public_fully.pid,
            patron_pid=patron2_martigny_no_email.pid
        )
    )
    assert res.status_code == 200
    actions = data.get('action_applied')
    request_loan_pid = actions[LoanAction.REQUEST].get('pid')

    # checkout martigny item at a martigny location
    res, data = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item_lib_martigny.pid,
            patron_pid=patron_martigny_no_email.pid
        )
    )
    assert res.status_code == 200
    actions = data.get('action_applied')
    loan_pid = actions[LoanAction.CHECKOUT].get('pid')

    # checkin item at saxon will raise an error multiple loans
    # the checkin loan is cancelled
    res, _ = postdata(
        client,
        'api_item.checkin',
        dict(
            item_pid=item_lib_martigny.pid,
            transaction_location_pid=loc_public_saxon.pid,
            pid=loan_pid
        ),
    )
    assert res.status_code == 200
    assert Loan.get_record_by_pid(loan_pid).get('state') == 'CANCELLED'
    # The request loan will automatically go in transit
    assert Loan.get_record_by_pid(request_loan_pid).get('state') == \
        'ITEM_IN_TRANSIT_FOR_PICKUP'


def test_auto_checkin_else(client, librarian_martigny_no_email,
                           patron_martigny_no_email, loc_public_martigny,
                           item3_lib_martigny, json_header,
                           loc_public_saxon):
    """Test item automatic checkin other scenarios."""
    login_user_via_session(client, librarian_martigny_no_email.user)

    record, actions = item3_lib_martigny.automatic_checkin()
    assert 'no' in actions

    res, data = postdata(
        client,
        'api_item.librarian_request',
        dict(
            item_pid=item3_lib_martigny.pid,
            pickup_location_pid=loc_public_saxon.pid,
            patron_pid=patron_martigny_no_email.pid
        ),
    )
    assert res.status_code == 200
    loan_pid = data.get('action_applied')[LoanAction.REQUEST].get('pid')

    res, _ = postdata(
        client,
        'api_item.validate_request',
        dict(
            item_pid=item3_lib_martigny.pid,
            pid=loan_pid,
            transaction_location_pid=loc_public_martigny.pid
        ),
    )
    assert res.status_code == 200

    item = Item.get_record_by_pid(item3_lib_martigny.pid)
    assert item.status == ItemStatus.IN_TRANSIT

    record, actions = item.automatic_checkin()
    assert 'no' in actions
    assert actions['no']['pid'] == loan_pid

    item.cancel_loan(pid=loan_pid)
    assert item.status == ItemStatus.ON_SHELF


def test_checkout_in_transit_return_same_library(
        client, librarian_martigny_no_email, librarian_saxon_no_email,
        patron_martigny_no_email, loc_public_martigny,
        item_type_standard_martigny, loc_public_saxon, item2_lib_martigny,
        json_header, circulation_policies):
    """Test item checkout, in-transit, checkin scenarios."""
    login_user_via_session(client, librarian_martigny_no_email.user)
    # checkout the item at location A
    res, data = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item2_lib_martigny.pid,
            patron_pid=patron_martigny_no_email.pid,
            transaction_location_pid=loc_public_martigny.pid
        )
    )
    assert res.status_code == 200
    item_data = data.get('metadata')
    actions = data.get('action_applied')
    assert item_data.get('status') == ItemStatus.ON_LOAN
    loan_pid = actions[LoanAction.CHECKOUT].get('pid')

    # checkin the item at location B
    res, data = postdata(
        client,
        'api_item.checkin',
        dict(
            item_pid=item2_lib_martigny.pid,
            pid=loan_pid,
            transaction_location_pid=loc_public_saxon.pid
        )
    )
    assert res.status_code == 200
    item_data = data.get('metadata')
    item = Item.get_record_by_pid(item_data.get('pid'))
    assert item.get('status') == ItemStatus.IN_TRANSIT

    # checkin the item at location A
    res, data = postdata(
        client,
        'api_item.automatic_checkin',
        dict(
            item_pid=item2_lib_martigny.pid,
            pid=loan_pid,
            transaction_location_pid=loc_public_martigny.pid
        )
    )
    assert res.status_code == 200
    item_data = data.get('metadata')
    item = Item.get_record_by_pid(item2_lib_martigny.pid)
    assert item.get('status') == ItemStatus.ON_SHELF
