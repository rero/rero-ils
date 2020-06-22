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

"""Test item circulation extend actions."""


import pytest
from invenio_circulation.errors import MultipleLoansOnItemError, \
    NoValidTransitionAvailableError
from utils import item_record_to_a_specific_loan_state

from rero_ils.modules.errors import NoCirculationAction
from rero_ils.modules.items.models import ItemStatus
from rero_ils.modules.loans.api import LoanState


def test_extend_on_item_on_shelf(
        item_lib_martigny, patron_martigny_no_email,
        loc_public_martigny, librarian_martigny_no_email,
        circulation_policies):
    """Test extend an on_shelf item."""
    # the following tests the circulation action EXTEND_1
    # for an on_shelf item, the extend action is not possible.

    params = {
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny_no_email.pid
    }
    with pytest.raises(NoCirculationAction):
        item, actions = item_lib_martigny.extend_loan(**params)
    assert item_lib_martigny.status == ItemStatus.ON_SHELF


def test_extend_on_item_at_desk(
        item_at_desk_martigny_patron_and_loan_at_desk,
        loc_public_martigny, librarian_martigny_no_email,
        circulation_policies):
    """Test extend an at_desk item."""
    # the following tests the circulation action EXTEND_2
    # for an at_desk item, the extend action is not possible.
    item, patron, loan = item_at_desk_martigny_patron_and_loan_at_desk
    # test fails if no loan pid is given
    params = {
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny_no_email.pid
    }
    with pytest.raises(NoCirculationAction):
        item, actions = item.extend_loan(**params)
    assert item.status == ItemStatus.AT_DESK
    # test fails if a loan pid is given
    params = {
        'pid': loan.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny_no_email.pid
    }
    with pytest.raises(NoValidTransitionAvailableError):
        item, actions = item.extend_loan(**params)
    assert item.status == ItemStatus.AT_DESK


def test_extend_on_item_on_loan_with_no_requests(
        item_on_loan_martigny_patron_and_loan_on_loan,
        loc_public_martigny, librarian_martigny_no_email,
        circulation_policies):
    """Test extend an on_loan item."""
    # the following tests the circulation action EXTEND_3_1
    # for an on_loan item with no requests, the extend action is possible.
    item, patron, loan = item_on_loan_martigny_patron_and_loan_on_loan

    params = {
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny_no_email.pid
    }
    item, actions = item.extend_loan(**params)
    assert item.status == ItemStatus.ON_LOAN


def test_extend_on_item_on_loan_with_requests(
        item_on_loan_martigny_patron_and_loan_on_loan,
        loc_public_martigny, librarian_martigny_no_email,
        circulation_policies, patron2_martigny_no_email):
    """Test extend an on_loan item with requests."""
    # the following tests the circulation action EXTEND_3_2
    # for an on_loan item with requests, the extend action is not possible.
    item, patron, loan = item_on_loan_martigny_patron_and_loan_on_loan

    params = {
        'patron_pid': patron2_martigny_no_email.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny_no_email.pid,
        'pickup_location_pid': loc_public_martigny.pid
    }
    item, requested_loan = item_record_to_a_specific_loan_state(
        item=item, loan_state=LoanState.PENDING, params=params,
        copy_item=False)
    # test fails if no loan pid is given
    params = {
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny_no_email.pid
    }
    with pytest.raises(NoCirculationAction):
        item, actions = item.extend_loan(**params)
    assert item.status == ItemStatus.ON_LOAN
    # test fails if loan pid is given
    params = {
        'pid': loan.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny_no_email.pid
    }
    with pytest.raises(NoCirculationAction):
        item, actions = item.extend_loan(**params)
    assert item.status == ItemStatus.ON_LOAN


def test_extend_on_item_in_transit_for_pickup(
        item_in_transit_martigny_patron_and_loan_for_pickup,
        loc_public_martigny, librarian_martigny_no_email,
        circulation_policies):
    """Test extend an in_transit for pickup item."""
    # the following tests the circulation action EXTEND_4
    # for an in_transit item, the extend action is not possible.
    item, patron, loan = item_in_transit_martigny_patron_and_loan_for_pickup
    # test fails if no loan pid is given
    params = {
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny_no_email.pid
    }
    with pytest.raises(NoCirculationAction):
        item, actions = item.extend_loan(**params)
    assert item.status == ItemStatus.IN_TRANSIT
    # test fails if a loan pid is given
    params = {
        'pid': loan.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny_no_email.pid
    }
    with pytest.raises(NoValidTransitionAvailableError):
        item, actions = item.extend_loan(**params)
    assert item.status == ItemStatus.IN_TRANSIT


def test_extend_on_item_in_transit_to_house(
        item_in_transit_martigny_patron_and_loan_to_house,
        loc_public_martigny, librarian_martigny_no_email,
        circulation_policies):
    """Test extend an in_transit to_house item."""
    # the following tests the circulation action EXTEND_4
    # for an in_transit item, the extend action is not possible.
    item, patron, loan = item_in_transit_martigny_patron_and_loan_to_house
    # test fails if no loan pid is given
    params = {
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny_no_email.pid
    }
    with pytest.raises(NoCirculationAction):
        item, actions = item.extend_loan(**params)
    assert item.status == ItemStatus.IN_TRANSIT
    # test fails if a loan pid is given
    params = {
        'pid': loan.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny_no_email.pid
    }
    with pytest.raises(NoValidTransitionAvailableError):
        item, actions = item.extend_loan(**params)
    assert item.status == ItemStatus.IN_TRANSIT
