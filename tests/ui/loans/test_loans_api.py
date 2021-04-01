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

"""CircPolicy Record tests."""

from __future__ import absolute_import, print_function

from copy import deepcopy
from datetime import date, datetime, timedelta, timezone

import ciso8601
from freezegun import freeze_time
from invenio_circulation.proxies import current_circulation
from invenio_circulation.search.api import LoansSearch
from utils import flush_index, get_mapping

from rero_ils.modules.circ_policies.api import DUE_SOON_REMINDER_TYPE
from rero_ils.modules.libraries.api import Library
from rero_ils.modules.loans.api import Loan, LoanState, get_loans_by_patron_pid
from rero_ils.modules.loans.tasks import loan_anonymizer
from rero_ils.modules.loans.utils import get_circ_policy, \
    get_default_loan_duration, sum_for_fees
from rero_ils.modules.notifications.api import Notification, \
    NotificationsSearch
from rero_ils.modules.notifications.tasks import create_notifications
from rero_ils.modules.patron_transactions.api import PatronTransaction


def test_loan_es_mapping(es_clear, db):
    """Test loans elasticsearch mapping."""
    search = current_circulation.loan_search_cls
    mapping = get_mapping(search.Meta.index)
    assert mapping == get_mapping(search.Meta.index)


def test_loans_create(loan_pending_martigny):
    """Test loan creation."""
    assert loan_pending_martigny.get('state') == LoanState.PENDING


def test_item_loans_elements(
        loan_pending_martigny, item_lib_fully, circ_policy_default_martigny):
    """Test loan elements."""
    assert loan_pending_martigny.item_pid == item_lib_fully.pid
    loan = list(get_loans_by_patron_pid(loan_pending_martigny.patron_pid))[0]
    assert loan.pid == loan_pending_martigny.get('pid')

    new_loan = deepcopy(loan_pending_martigny)
    del new_loan['transaction_location_pid']
    assert get_default_loan_duration(new_loan, None) == \
        get_default_loan_duration(loan_pending_martigny, None)

    assert item_lib_fully.last_location_pid == item_lib_fully.location_pid
    del circ_policy_default_martigny['checkout_duration']
    circ_policy_default_martigny.update(
        circ_policy_default_martigny, dbcommit=True, reindex=True)


def test_is_due_soon(
        item_on_loan_martigny_patron_and_loan_on_loan):
    """Test 'is due soon' method about a loan."""
    item, patron, loan = item_on_loan_martigny_patron_and_loan_on_loan

    # Just after creation the loan isn't yet 'due_soon'.
    # the corresponding circulation policy define a due_soon notification.
    assert not loan.is_loan_due_soon()
    cipo = get_circ_policy(loan)
    reminder = cipo.get_reminder(reminder_type=DUE_SOON_REMINDER_TYPE)
    assert reminder.get('days_delay')

    # mock the sysdate to just 5 days before the due_date
    due_date = ciso8601.parse_datetime(loan.end_date)
    mock_date = due_date - timedelta(days=reminder.get('days_delay'))
    with freeze_time(mock_date):
        assert loan.is_loan_due_soon()


def test_loan_keep_and_to_anonymize(
        item_on_loan_martigny_patron_and_loan_on_loan,
        item2_on_loan_martigny_patron_and_loan_on_loan,
        librarian_martigny, loc_public_martigny):
    """Test anonymize and keep loan based on open transactions."""
    item, patron, loan = item_on_loan_martigny_patron_and_loan_on_loan
    assert not loan.concluded(loan)
    assert not loan.can_anonymize(loan_data=loan)

    params = {
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    item.checkin(**params)
    loan = Loan.get_record_by_pid(loan.pid)
    # item checkedin and has no open events
    assert loan.concluded(loan)
    assert not loan.can_anonymize(loan_data=loan)

    patron.user.profile.keep_history = False
    # when the patron asks to anonymise history the can_anonymize is true
    loan = Loan.get_record_by_pid(loan.pid)
    assert loan.concluded(loan)
    assert loan.can_anonymize(loan_data=loan)
    loan.update(loan, dbcommit=True, reindex=True)

    # test loans with fees
    item, patron, loan = item2_on_loan_martigny_patron_and_loan_on_loan
    assert not loan.concluded(loan)
    assert not loan.can_anonymize(loan_data=loan)
    end_date = datetime.now(timezone.utc) - timedelta(days=7)
    loan['end_date'] = end_date.isoformat()
    loan.update(loan, dbcommit=True, reindex=True)

    create_notifications(types=[
        Notification.DUE_SOON_NOTIFICATION_TYPE,
        Notification.OVERDUE_NOTIFICATION_TYPE
    ])
    flush_index(NotificationsSearch.Meta.index)
    flush_index(LoansSearch.Meta.index)

    params = {
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    item.checkin(**params)
    loan = Loan.get_record_by_pid(loan.pid)

    assert not loan.concluded(loan)
    assert not loan.can_anonymize(loan_data=loan)


def test_anonymizer_job(
        item_on_loan_martigny_patron_and_loan_on_loan,
        librarian_martigny, loc_public_martigny):
    """Test loan anonymizer job."""
    msg = loan_anonymizer(dbcommit=True, reindex=True)

    item, patron, loan = item_on_loan_martigny_patron_and_loan_on_loan
    # make the loan overdue
    end_date = datetime.now(timezone.utc) - timedelta(days=10)
    loan['end_date'] = end_date.isoformat()
    loan.update(loan, dbcommit=True, reindex=True)

    create_notifications(types=[
        Notification.DUE_SOON_NOTIFICATION_TYPE,
        Notification.OVERDUE_NOTIFICATION_TYPE
    ])
    flush_index(NotificationsSearch.Meta.index)
    flush_index(LoansSearch.Meta.index)

    assert not loan.concluded(loan)
    assert not loan.can_anonymize(loan_data=loan)

    patron.user.profile.keep_history = True

    params = {
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    item.checkin(**params)
    loan = Loan.get_record_by_pid(loan.pid)
    # item checked-in and has no open events
    assert not loan.concluded(loan)
    assert not loan.can_anonymize(loan_data=loan)

    msg = loan_anonymizer(dbcommit=True, reindex=True)
    assert msg == 'number_of_loans_anonymized: 0'

    patron.user.profile.keep_history = False
    # close open transactions and notifications
    for transaction in PatronTransaction.get_transactions_by_patron_pid(
                patron.get('pid'), 'open'):
        transaction = PatronTransaction.get_record_by_pid(transaction.pid)
        transaction['status'] = 'closed'
        transaction.update(transaction, dbcommit=True, reindex=True)
    msg = loan_anonymizer(dbcommit=True, reindex=True)
    assert msg == 'number_of_loans_anonymized: 2'


def test_loan_get_overdue_fees(item_on_loan_martigny_patron_and_loan_on_loan):
    """Test the overdue fees computation."""

    def get_end_date(delta=0):
        end = date.today() - timedelta(days=delta)
        end = datetime(end.year, end.month, end.day, tzinfo=timezone.utc)
        return end - timedelta(microseconds=1)

    _, _, loan = item_on_loan_martigny_patron_and_loan_on_loan
    cipo = get_circ_policy(loan)
    library = Library.get_record_by_pid(loan.library_pid)

    # CASE#1 :: classic settings.
    #    * 3 intervals with no gap into each one.
    #    * no limit on last interval
    #    * no maximum overdue
    cipo['overdue_fees'] = {
        'intervals': [
            {'from': 1, 'to': 1, 'fee_amount': 0.10},
            {'from': 2, 'to': 2, 'fee_amount': 0.20},
            {'from': 3, 'fee_amount': 0.50},
        ]
    }
    cipo.update(data=cipo, dbcommit=True, reindex=True)
    expected_due_amount = [0.1, 0.3, 0.8, 1.3, 1.8, 2.3, 2.8, 3.3, 3.8, 4.3]
    for delta in range(0, len(expected_due_amount)):
        end = get_end_date(delta)
        loan['end_date'] = end.isoformat()
        loan = loan.update(loan, dbcommit=True, reindex=True)
        count_open = library.count_open(start_date=end + timedelta(days=1))
        if count_open == 0:
            continue
        assert sum_for_fees(loan.get_overdue_fees) == \
               expected_due_amount[count_open - 1]

    # CASE#2 :: no more overdue after 3 days.
    #    * same definition than before, but add a upper limit to the last
    #      interval
    cipo['overdue_fees'] = {
        'intervals': [
            {'from': 1, 'to': 1, 'fee_amount': 0.10},
            {'from': 2, 'to': 2, 'fee_amount': 0.20},
            {'from': 3, 'to': 3, 'fee_amount': 0.50},
        ]
    }
    cipo.update(data=cipo, dbcommit=True, reindex=True)
    expected_due_amount = [0.1, 0.3, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8]
    for delta in range(0, len(expected_due_amount)):
        end = get_end_date(delta)
        loan['end_date'] = end.isoformat()
        loan = loan.update(loan, dbcommit=True, reindex=True)
        count_open = library.count_open(start_date=end + timedelta(days=1))
        if count_open == 0:
            continue
        assert sum_for_fees(loan.get_overdue_fees) == \
               expected_due_amount[count_open - 1]

    # CASE#3 :: classic setting + maximum overdue.
    #    * 3 intervals with no gap into each one.
    #    * no limit on last interval
    #    * maximum overdue = 2
    cipo['overdue_fees'] = {
        'intervals': [
            {'from': 1, 'to': 1, 'fee_amount': 0.10},
            {'from': 2, 'to': 2, 'fee_amount': 0.20},
            {'from': 3, 'fee_amount': 0.50},
        ],
        'maximum_total_amount': 2
    }
    cipo.update(data=cipo, dbcommit=True, reindex=True)
    expected_due_amount = [0.1, 0.3, 0.8, 1.3, 1.8, 2.0, 2.0, 2.0, 2.0, 2.0]
    for delta in range(0, len(expected_due_amount)):
        end = get_end_date(delta)
        loan['end_date'] = end.isoformat()
        loan = loan.update(loan, dbcommit=True, reindex=True)
        count_open = library.count_open(start_date=end + timedelta(days=1))
        if count_open == 0:
            continue
        assert sum_for_fees(loan.get_overdue_fees) == \
               expected_due_amount[count_open - 1]

    # CASE#4 :: intervals with gaps
    #    * define 2 intervals with gaps between
    #    * grace period for first overdue day
    #    * maximum overdue to 2.5 (not a normal step)
    cipo['overdue_fees'] = {
        'intervals': [
            {'from': 2, 'to': 3, 'fee_amount': 0.10},
            {'from': 5, 'fee_amount': 0.50}
        ],
        'maximum_total_amount': 1.1
    }
    cipo.update(data=cipo, dbcommit=True, reindex=True)
    expected_due_amount = [0, 0.1, 0.2, 0.2, 0.7, 1.1, 1.1, 1.1, 1.1, 1.1, 1.1]
    for delta in range(0, len(expected_due_amount)):
        end = get_end_date(delta)
        loan['end_date'] = end.isoformat()
        loan = loan.update(loan, dbcommit=True, reindex=True)
        count_open = library.count_open(start_date=end + timedelta(days=1))
        if count_open == 0:
            continue
        assert sum_for_fees(loan.get_overdue_fees) == \
               expected_due_amount[count_open-1]

    # RESET THE CIPO
    del cipo['overdue_fees']
    cipo.update(data=cipo, dbcommit=True, reindex=True)
