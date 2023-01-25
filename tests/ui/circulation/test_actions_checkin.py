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

"""Test item circulation checkin actions."""
from datetime import timedelta

import ciso8601
import pytest
from freezegun import freeze_time
from utils import item_record_to_a_specific_loan_state

from rero_ils.modules.errors import NoCirculationAction
from rero_ils.modules.items.api import Item
from rero_ils.modules.items.api.api import ItemsSearch
from rero_ils.modules.items.models import ItemStatus
from rero_ils.modules.loans.api import Loan
from rero_ils.modules.loans.models import LoanAction, LoanState


def test_checkin_on_item_on_shelf_no_requests(
        item_lib_martigny, patron_martigny, lib_martigny,
        loc_public_martigny, librarian_martigny, lib_fully,
        patron2_martigny, loc_public_fully, circulation_policies):
    """Test checkin on an on_shelf item with no requests."""
    # the following tests the circulation action CHECKIN_1_1_1
    # an on_shelf item with no pending requests. when the item library equal
    # to the transaction library, there is no checkin action possible.
    # no circulation action will be performed.
    params = {
        'transaction_library_pid': lib_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    with pytest.raises(NoCirculationAction):
        item, actions = item_lib_martigny.checkin(**params)
        assert item.status == ItemStatus.ON_SHELF

    # the following tests the circulation action CHECKIN_1_1_2
    # for an item on_shelf with no pending loans, the item library does not
    # equal to the transaction library, the item assigned the in_transit
    # status and no circulation action will be performed.
    params['transaction_library_pid'] = lib_fully.pid
    with pytest.raises(NoCirculationAction):
        item, actions = item_lib_martigny.checkin(**params)
    item = Item.get_record_by_pid(item_lib_martigny.pid)
    assert item.status == ItemStatus.IN_TRANSIT
    params['transaction_library_pid'] = lib_martigny.pid
    with pytest.raises(NoCirculationAction):
        item, actions = item_lib_martigny.checkin(**params)
    item = Item.get_record_by_pid(item_lib_martigny.pid)
    assert item.status == ItemStatus.ON_SHELF


def test_checkin_on_item_on_shelf_with_requests(
        item_on_shelf_martigny_patron_and_loan_pending,
        loc_public_martigny, librarian_martigny, item_lib_martigny_data,
        patron2_martigny, loc_public_fully, lib_martigny):
    """Test checkin on an on_shelf item with requests."""
    item, patron, loan = item_on_shelf_martigny_patron_and_loan_pending
    # the following tests the circulation action CHECKIN_1_2_1
    # for an item on_shelf with pending loans, the pickup library of the first
    # pending loan equal to the transaction library, the first pending loan
    # is validated and item assigned the at_desk
    # validate_request circulation action will be performed.

    # create a second pending loan on same item
    item_pid = item_lib_martigny_data.get('pid')
    item_es = ItemsSearch().filter('term', pid=item_pid)\
        .execute().hits.hits[0]._source
    assert item_es['current_pending_requests'] == 0
    params = {
        'patron_pid': patron2_martigny.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid,
        'pickup_location_pid': loc_public_fully.pid
    }
    item, requested_loan = item_record_to_a_specific_loan_state(
        item=item, loan_state=LoanState.PENDING,
        params=params, copy_item=False)
    assert requested_loan['state'] == LoanState.PENDING
    item_es = ItemsSearch().filter('term', pid=item.pid)\
        .execute().hits.hits[0]._source
    assert item_es['current_pending_requests'] == 2

    params = {
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    item, actions = item.checkin(**params)
    assert item.status == ItemStatus.AT_DESK
    assert Loan.get_record_by_pid(loan.pid)['state'] == LoanState.ITEM_AT_DESK
    assert Loan.get_record_by_pid(requested_loan.pid)['state'] == \
        LoanState.PENDING


def test_checkin_on_item_on_shelf_with_requests_external(
        item_on_shelf_fully_patron_and_loan_pending,
        loc_public_fully, librarian_martigny,
        patron2_martigny, lib_martigny, loc_public_martigny):
    """Test checkin on an on_shelf item with requests."""
    item, patron, loan = item_on_shelf_fully_patron_and_loan_pending
    # the following tests the circulation action CHECKIN_1_2_2
    # for an item on_shelf with pending loans, the pickup library of the first
    # pending loan does not equal to the transaction library, the first pending
    # loan is validated and item assigned the in_transit
    # validate_request circulation action will be performed.

    # create a second pending loan on same item
    params = {
        'patron_pid': patron2_martigny.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid,
        'pickup_location_pid': loc_public_martigny.pid
    }
    item, requested_loan = item_record_to_a_specific_loan_state(
        item=item, loan_state=LoanState.PENDING,
        params=params, copy_item=False)
    assert requested_loan['state'] == LoanState.PENDING

    params = {
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    item, actions = item.checkin(**params)
    item = Item.get_record_by_pid(item.pid)
    assert item.status == ItemStatus.IN_TRANSIT
    assert Loan.get_record_by_pid(loan.pid)['state'] == \
        LoanState.ITEM_IN_TRANSIT_FOR_PICKUP
    assert Loan.get_record_by_pid(requested_loan.pid)['state'] == \
        LoanState.PENDING


def test_checkin_on_item_at_desk(
        item_at_desk_martigny_patron_and_loan_at_desk,
        librarian_martigny, loc_public_fully,
        lib_martigny, loc_public_martigny):
    """Test checkin on an at_desk item."""
    item, patron, loan = item_at_desk_martigny_patron_and_loan_at_desk
    # the following tests the circulation action CHECKIN_2_1
    # for an item at_desk, the pickup library of the
    # item_at_desk loan does equal to the transaction library
    # no action is done, item remains at_desk
    params = {
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    with pytest.raises(NoCirculationAction):
        item, actions = item.checkin(**params)
        assert item.status == ItemStatus.AT_DESK

    # the following tests the circulation action CHECKIN_2_2
    # for an item at_desk, the pickup library of the
    # item_at_desk loan does not equal to the transaction library
    # item received the in_transit status and the loan change its status
    # to IN_TRANSIT_FOR_PICKUP

    params = {
        'transaction_location_pid': loc_public_fully.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    with pytest.raises(NoCirculationAction):
        item, actions = item.checkin(**params)
        assert item.status == ItemStatus.IN_TRANSIT
        assert loan['state'] == LoanState.IN_TRANSIT_FOR_PICKUP


def test_checkin_on_item_on_loan(
        item_on_loan_martigny_patron_and_loan_on_loan,
        item2_on_loan_martigny_patron_and_loan_on_loan,
        item_on_loan_fully_patron_and_loan_on_loan, loc_public_fully,
        loc_public_martigny, librarian_martigny):
    """Test checkin on an on_loan item."""
    item, patron, loan = item_on_loan_martigny_patron_and_loan_on_loan
    # the following tests the circulation action CHECKIN_3_1_1
    # for an item on_loan, the item library equal the transaction library,
    # checkin the item and item becomes on_shelf
    # case when the loan pid is given as a parameter
    params = {
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid,
        'pid': loan.pid
    }
    item, actions = item.checkin(**params)
    item = Item.get_record_by_pid(item.pid)
    loan = Loan.get_record_by_pid(loan.pid)
    assert item.status == ItemStatus.ON_SHELF
    assert loan['state'] == LoanState.ITEM_RETURNED

    # case when the loan pid is not given as a parameter
    item, patron, loan = item_on_loan_fully_patron_and_loan_on_loan
    params = {
        'transaction_location_pid': loc_public_fully.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    item, actions = item.checkin(**params)
    item = Item.get_record_by_pid(item.pid)
    loan = Loan.get_record_by_pid(loan.pid)
    assert item.status == ItemStatus.ON_SHELF
    assert loan['state'] == LoanState.ITEM_RETURNED

    # the following tests the circulation action CHECKIN_3_1_2
    # for an item on_loan, the item library does not equal the transaction
    # library, checkin the item and item becomes in_transit
    item, patron, loan = item2_on_loan_martigny_patron_and_loan_on_loan
    params = {
        'transaction_location_pid': loc_public_fully.pid,
        'transaction_user_pid': librarian_martigny.pid,
        'pid': loan.pid
    }
    item, actions = item.checkin(**params)
    item = Item.get_record_by_pid(item.pid)
    loan = Loan.get_record_by_pid(loan.pid)
    assert item.status == ItemStatus.IN_TRANSIT
    assert loan['state'] == LoanState.ITEM_IN_TRANSIT_TO_HOUSE


def test_checkin_on_item_on_loan_with_requests(
        item3_on_loan_martigny_patron_and_loan_on_loan,
        loc_public_martigny, librarian_martigny,
        patron2_martigny):
    """Test checkin on an on_loan item with requests at local library."""
    # the following tests the circulation action CHECKIN_3_2_1
    # for an item on_loan, with pending requests. when the pickup library of
    # the first pending request equal to the transaction library,
    # checkin the item and item becomes at_desk.
    # the on_loan is returned and validating the first pending loan request.
    #
    # In this test, we will also ensure that the request expiration date of the
    # automatic validated request is correct
    item, patron, loan = item3_on_loan_martigny_patron_and_loan_on_loan

    # create a request on the same item one day after the first loan
    tomorrow = ciso8601.parse_datetime(loan['start_date']) + timedelta(days=10)
    with freeze_time(tomorrow.isoformat()):
        item, actions = item.request(
            pickup_location_pid=loc_public_martigny.pid,
            patron_pid=patron2_martigny.pid,
            transaction_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny.pid
        )
        requested_loan_pid = actions[LoanAction.REQUEST].get('pid')
        requested_loan = Loan.get_record_by_pid(requested_loan_pid)

    # Check-in the item
    #  * reload item, loan and requested_loan
    #  * ensure the item is still AT_DESK (because the first pending request
    #    has been automatically validate and pickup location is the same than
    #    previous loan location)
    #  * ensure first loan is concluded
    #  * ensure the requested loan is now "AT_DESK" with a valid request
    #    expiration date
    next_day = tomorrow + timedelta(days=10)
    with freeze_time(next_day.isoformat()):
        item, actions = item.checkin(
            patron_pid=patron2_martigny.pid,
            transaction_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny.pid,
            pickup_location_pid=loc_public_martigny.pid
        )

    item = Item.get_record_by_pid(item.pid)
    loan = Loan.get_record_by_pid(loan.pid)
    requested_loan = Loan.get_record_by_pid(requested_loan.pid)

    assert item.status == ItemStatus.AT_DESK
    assert loan['state'] == LoanState.ITEM_RETURNED
    assert requested_loan['state'] == LoanState.ITEM_AT_DESK
    trans_date = ciso8601.parse_datetime(requested_loan['transaction_date'])
    assert trans_date.strftime('%Y%m%d') == next_day.strftime('%Y%m%d')


def test_checkin_on_item_on_loan_with_requests_externally(
        item4_on_loan_martigny_patron_and_loan_on_loan,
        item5_on_loan_martigny_patron_and_loan_on_loan,
        loc_public_martigny, librarian_martigny,
        patron2_martigny, loc_public_fully, loc_public_saxon):
    """Test checkin on an on_loan item with requests at an external library."""
    item, patron, loan = item4_on_loan_martigny_patron_and_loan_on_loan
    # the following tests the circulation action CHECKIN_3_2_2_1
    # for an item on_loan, with pending requests. when the pickup library of
    # the first pending request does not equal to the transaction library,
    # checkin the item and the loan on_loan is cancelled.
    # if the pickup location of the first pending equal the item library,
    # the pending loan becomes ITEM_IN_TRANSIT_FOR_PICKUP

    params = {
        'patron_pid': patron2_martigny.pid,
        'transaction_location_pid': loc_public_fully.pid,
        'transaction_user_pid': librarian_martigny.pid,
        'pickup_location_pid': loc_public_martigny.pid
    }

    item, requested_loan = item_record_to_a_specific_loan_state(
        item=item, loan_state=LoanState.PENDING, params=params,
        copy_item=False)

    item, actions = item.checkin(**params)
    item = Item.get_record_by_pid(item.pid)
    loan = Loan.get_record_by_pid(loan.pid)
    requested_loan = Loan.get_record_by_pid(requested_loan.pid)
    assert item.status == ItemStatus.IN_TRANSIT
    assert loan['state'] == LoanState.CANCELLED
    assert requested_loan['state'] == LoanState.ITEM_IN_TRANSIT_FOR_PICKUP

    item, patron, loan = item5_on_loan_martigny_patron_and_loan_on_loan
    # the following tests the circulation action CHECKIN_3_2_2_2
    # for an item on_loan, with pending requests. when the pickup library of
    # the first pending request does not equal to the transaction library,
    # checkin the item and the loan on_loan is cancelled.
    # if the pickup location of the first pending does not equal the item
    # library, the pending loan becomes ITEM_IN_TRANSIT_FOR_PICKUP

    params = {
        'patron_pid': patron2_martigny.pid,
        'transaction_location_pid': loc_public_saxon.pid,
        'transaction_user_pid': librarian_martigny.pid,
        'pickup_location_pid': loc_public_fully.pid
    }

    item, requested_loan = item_record_to_a_specific_loan_state(
        item=item, loan_state=LoanState.PENDING, params=params,
        copy_item=False)

    item, actions = item.checkin(**params)
    item = Item.get_record_by_pid(item.pid)
    loan = Loan.get_record_by_pid(loan.pid)
    requested_loan = Loan.get_record_by_pid(requested_loan.pid)
    assert item.status == ItemStatus.IN_TRANSIT
    assert loan['state'] == LoanState.CANCELLED
    assert requested_loan['state'] == LoanState.ITEM_IN_TRANSIT_FOR_PICKUP


def test_checkin_on_item_in_transit_for_pickup(
        item_in_transit_martigny_patron_and_loan_for_pickup,
        loc_public_martigny, librarian_martigny,
        loc_public_fully):
    """Test checkin on an in_transit item for pickup."""
    item, patron, loan = item_in_transit_martigny_patron_and_loan_for_pickup

    # the following tests the circulation action CHECKIN_4_1
    # for an item in_transit (loan=ITEM_IN_TRANSIT_FOR_PICKUP). when the pickup
    # library of the loan does equal to the transaction library, automatic
    # receive of the item is done and the loan becomes ITEM_AT_DESK, the item
    # becomes at_desk
    params = {
        'patron_pid': patron.pid,
        'transaction_location_pid': loc_public_fully.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    item, actions = item.checkin(**params)
    item = Item.get_record_by_pid(item.pid)
    loan = Loan.get_record_by_pid(loan.pid)
    assert item.status == ItemStatus.AT_DESK
    assert loan['state'] == LoanState.ITEM_AT_DESK


def test_checkin_on_item_in_transit_for_pickup_externally(
        item2_in_transit_martigny_patron_and_loan_for_pickup,
        loc_public_martigny, librarian_martigny,
        loc_public_fully, loc_public_saxon):
    """Test checkin on an in_transit item for pickup."""
    item, patron, loan = item2_in_transit_martigny_patron_and_loan_for_pickup

    # the following tests the circulation action CHECKIN_4_2
    # for an item in_transit (loan=ITEM_IN_TRANSIT_FOR_PICKUP). when the pickup
    # library of the loan does not equal to the transaction library, no action
    # is done, the item remains in_transit
    params = {
        'patron_pid': patron.pid,
        'transaction_location_pid': loc_public_saxon.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    with pytest.raises(NoCirculationAction):
        item, actions = item.checkin(**params)
    item = Item.get_record_by_pid(item.pid)
    loan = Loan.get_record_by_pid(loan.pid)
    assert item.status == ItemStatus.IN_TRANSIT
    assert loan['state'] == LoanState.ITEM_IN_TRANSIT_FOR_PICKUP


def test_checkin_on_item_in_transit_to_house(
        item_in_transit_martigny_patron_and_loan_to_house,
        loc_public_martigny, librarian_martigny):
    """Test checkin on an in_transit item to house."""
    item, patron, loan = item_in_transit_martigny_patron_and_loan_to_house

    # the following tests the circulation action CHECKIN_5_1_1
    # for an item in_transit (loan=IN_TRANSIT_TO_HOUSE). when the transaction
    # library does equal to the item library, will receive the item.
    # the item becomes on_shelf and the loan is terminated.
    params = {
        'patron_pid': patron.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    item, actions = item.checkin(**params)
    item = Item.get_record_by_pid(item.pid)
    loan = Loan.get_record_by_pid(loan.pid)
    assert item.status == ItemStatus.ON_SHELF
    assert loan['state'] == LoanState.ITEM_RETURNED


def test_checkin_on_item_in_transit_to_house_externally(
        item2_in_transit_martigny_patron_and_loan_to_house,
        loc_public_martigny, librarian_martigny, loc_public_saxon):
    """Test checkin on an in_transit item to house."""
    item, patron, loan = item2_in_transit_martigny_patron_and_loan_to_house

    # the following tests the circulation action CHECKIN_5_1_2
    # for an item in_transit (loan=IN_TRANSIT_TO_HOUSE). when the transaction
    # library does not equal to the item library, will receive the item.
    # the item becomes on_shelf and the loan is terminated.
    params = {
        'patron_pid': patron.pid,
        'transaction_location_pid': loc_public_saxon.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    with pytest.raises(NoCirculationAction):
        item, actions = item.checkin(**params)
    item = Item.get_record_by_pid(item.pid)
    loan = Loan.get_record_by_pid(loan.pid)
    assert item.status == ItemStatus.IN_TRANSIT
    assert loan['state'] == LoanState.ITEM_IN_TRANSIT_TO_HOUSE


def test_checkin_on_item_in_transit_to_house_with_requests(
        item3_in_transit_martigny_patron_and_loan_to_house,
        loc_public_martigny, librarian_martigny,
        patron2_martigny):
    """Test checkin on an in_transit item to house."""
    item, patron, loan = item3_in_transit_martigny_patron_and_loan_to_house

    # the following tests the circulation action CHECKIN_5_2_1_1
    # for an item in_transit (loan=IN_TRANSIT_TO_HOUSE) with pending requests.
    # when the pickup library of the first pending request does equal to the
    # transaction library. and pickup library equals to the item library,
    # will receive the item.
    # the item becomes at_desk and the loan is terminated.
    # and will validate the first pending loan
    params = {
        'patron_pid': patron2_martigny.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid,
        'pickup_location_pid': loc_public_martigny.pid
    }
    item, requested_loan = item_record_to_a_specific_loan_state(
        item=item, loan_state=LoanState.PENDING,
        params=params, copy_item=False)
    assert requested_loan['state'] == LoanState.PENDING
    params = {
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid,
        'pickup_location_pid': loc_public_martigny.pid
    }

    item, actions = item.checkin(**params)
    item = Item.get_record_by_pid(item.pid)
    loan = Loan.get_record_by_pid(loan.pid)
    requested_loan = Loan.get_record_by_pid(requested_loan.pid)
    assert item.status == ItemStatus.AT_DESK
    assert loan['state'] == LoanState.ITEM_RETURNED
    assert requested_loan['state'] == LoanState.ITEM_AT_DESK


def test_checkin_on_item_in_transit_to_house_with_requests_externally(
        item4_in_transit_martigny_patron_and_loan_to_house,
        loc_public_martigny, librarian_martigny,
        patron2_martigny, loc_public_saxon):
    """Test checkin on an in_transit item to house."""
    item, patron, loan = item4_in_transit_martigny_patron_and_loan_to_house

    # the following tests the circulation action CHECKIN_5_2_1_2
    # for an item in_transit (loan=IN_TRANSIT_TO_HOUSE) with pending requests.
    # pickup location of first PENDING loan = transaction library
    # when the pickup library of the first pending request does not equal to
    # the to the item library, cancel the current loan.
    # the item becomes at_desk and will validate the first pending loan

    params = {
        'patron_pid': patron2_martigny.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid,
        'pickup_location_pid': loc_public_saxon.pid
    }
    item, requested_loan = item_record_to_a_specific_loan_state(
        item=item, loan_state=LoanState.PENDING,
        params=params, copy_item=False)
    assert requested_loan['state'] == LoanState.PENDING
    params = {
        'transaction_location_pid': loc_public_saxon.pid,
        'transaction_user_pid': librarian_martigny.pid
    }

    item, actions = item.checkin(**params)
    item = Item.get_record_by_pid(item.pid)
    loan = Loan.get_record_by_pid(loan.pid)
    requested_loan = Loan.get_record_by_pid(requested_loan.pid)
    assert item.status == ItemStatus.AT_DESK
    assert loan['state'] == LoanState.CANCELLED
    assert requested_loan['state'] == LoanState.ITEM_AT_DESK


def test_checkin_on_item_in_transit_to_house_with_external_loans(
        item5_in_transit_martigny_patron_and_loan_to_house,
        loc_public_martigny, librarian_martigny,
        patron2_martigny, loc_public_saxon):
    """Test checkin on an in_transit item to house."""
    item, patron, loan = item5_in_transit_martigny_patron_and_loan_to_house

    # the following tests the circulation action CHECKIN_5_2_2_1
    # for an item in_transit (loan=IN_TRANSIT_TO_HOUSE) with pending requests.
    # pickup location of first PENDING loan does not equal transaction library.
    # when the pickup library of the first pending request does equal to
    # the to the item library, no action performed.
    # the item remains at_desk
    params = {
        'patron_pid': patron2_martigny.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid,
        'pickup_location_pid': loc_public_martigny.pid
    }
    item, requested_loan = item_record_to_a_specific_loan_state(
        item=item, loan_state=LoanState.PENDING,
        params=params, copy_item=False)
    assert requested_loan['state'] == LoanState.PENDING
    params = {
        'transaction_location_pid': loc_public_saxon.pid,
        'transaction_user_pid': librarian_martigny.pid
    }

    with pytest.raises(NoCirculationAction):
        item, actions = item.checkin(**params)
    item = Item.get_record_by_pid(item.pid)
    loan = Loan.get_record_by_pid(loan.pid)
    requested_loan = Loan.get_record_by_pid(requested_loan.pid)
    assert item.status == ItemStatus.IN_TRANSIT
    assert loan['state'] == LoanState.ITEM_IN_TRANSIT_TO_HOUSE
    assert requested_loan['state'] == LoanState.PENDING


def test_checkin_on_item_in_transit_to_house_with_external_loans_transit(
        item6_in_transit_martigny_patron_and_loan_to_house,
        loc_public_martigny, librarian_martigny,
        patron2_martigny, loc_public_saxon, loc_public_saillon):
    """Test checkin on an in_transit item to house."""
    item, patron, loan = item6_in_transit_martigny_patron_and_loan_to_house

    # the following tests the circulation action CHECKIN_5_2_2_2
    # for an item in_transit (loan=IN_TRANSIT_TO_HOUSE) with pending requests.
    # pickup location of first PENDING loan does not equal transaction library.
    # when the pickup library of the first pending request does not equal to
    # the to the item library, will cancel the current loan and then validate
    # the first pending request. item becomes in_transit and becomes
    # ITEM_IN_TRANSIT_FOR_PICKUP
    params = {
        'patron_pid': patron2_martigny.pid,
        'transaction_location_pid': loc_public_saxon.pid,
        'transaction_user_pid': librarian_martigny.pid,
        'pickup_location_pid': loc_public_saxon.pid
    }
    item, requested_loan = item_record_to_a_specific_loan_state(
        item=item, loan_state=LoanState.PENDING,
        params=params, copy_item=False)
    assert requested_loan['state'] == LoanState.PENDING
    params = {
        'transaction_location_pid': loc_public_saillon.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    item, actions = item.checkin(**params)

    item = Item.get_record_by_pid(item.pid)
    loan = Loan.get_record_by_pid(loan.pid)
    requested_loan = Loan.get_record_by_pid(requested_loan.pid)
    assert item.status == ItemStatus.IN_TRANSIT
    assert loan['state'] == LoanState.CANCELLED
    assert requested_loan['state'] == LoanState.ITEM_IN_TRANSIT_FOR_PICKUP
