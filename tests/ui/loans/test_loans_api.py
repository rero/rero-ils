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
import mock
from freezegun import freeze_time
from invenio_circulation.proxies import current_circulation
from invenio_circulation.search.api import LoansSearch
from utils import flush_index, get_mapping

from rero_ils.modules.circ_policies.api import DUE_SOON_REMINDER_TYPE
from rero_ils.modules.items.models import ItemStatus
from rero_ils.modules.libraries.api import Library
from rero_ils.modules.loans.api import Loan, get_expired_request
from rero_ils.modules.loans.models import LoanAction, LoanState
from rero_ils.modules.loans.tasks import loan_anonymizer
from rero_ils.modules.loans.utils import get_circ_policy, \
    get_default_loan_duration, sum_for_fees
from rero_ils.modules.locations.api import Location
from rero_ils.modules.notifications.api import NotificationsSearch
from rero_ils.modules.notifications.models import NotificationType
from rero_ils.modules.notifications.tasks import create_notifications, \
    process_notifications
from rero_ils.modules.patron_transactions.api import PatronTransaction
from rero_ils.modules.patron_transactions.utils import \
    get_transactions_pids_for_patron


def test_loan_es_mapping(es_clear, db):
    """Test loans elasticsearch mapping."""
    search = current_circulation.loan_search_cls
    mapping = get_mapping(search.Meta.index)
    assert mapping == get_mapping(search.Meta.index)


def test_loans_create(loan_pending_martigny):
    """Test loan creation."""
    assert loan_pending_martigny.get('state') == LoanState.PENDING


def test_loans_properties(loan_pending_martigny, item_lib_fully):
    """Test loan properties."""
    loan = loan_pending_martigny
    assert loan.request_creation_date
    assert not loan.rank
    assert loan.item_pid_object['value'] == item_lib_fully.pid

    # pending transactions
    pid = loan.pop('pid')
    assert not loan.has_pending_transaction()
    loan['pid'] = pid
    # loan due soon
    assert not loan.is_loan_due_soon()
    # age
    transaction_date = loan.pop('transaction_date')
    assert loan.age() == 0
    loan['transaction_date'] = transaction_date


def test_loans_indexing(loan_pending_martigny, loc_public_martigny):
    """Test loan indexing."""
    loan = loan_pending_martigny
    assert loan.reindex()
    state = loan['state']
    loan['state'] = LoanState.CANCELLED
    loan.update(loan, True, True, True)
    flush_index(LoansSearch.Meta.index)
    loc_data = dict(loc_public_martigny)

    # indexing a terminated loan should work even if linked resources are
    # removed
    loc_public_martigny.delete(False, True, True)
    assert loan.reindex()

    # restore original data
    loc_public_martigny.delete(True, True, True)
    Location.create(loc_data, dbcommit=True, reindex=True)
    loan['state'] = state
    loan.update(loan, True, True, True)


def test_item_loans_default_duration(
        item_lib_martigny, librarian_martigny, patron_martigny,
        loc_public_martigny, circulation_policies, lib_martigny):
    """Test default loan duration."""

    # create a loan with request is easy
    item, actions = item_lib_martigny.request(
        pickup_location_pid=loc_public_martigny.pid,
        patron_pid=patron_martigny.pid,
        transaction_location_pid=loc_public_martigny.pid,
        transaction_user_pid=librarian_martigny.pid
    )
    loan_pid = actions['request']['pid']
    loan = Loan.get_record_by_pid(loan_pid)
    # a new loan without transaction location
    new_loan = deepcopy(loan)
    del new_loan['transaction_location_pid']
    # should have the same duration
    with freeze_time():
        assert get_default_loan_duration(new_loan, None) == \
            get_default_loan_duration(loan, None)

    policy = get_circ_policy(loan)
    # the checkout duration should be enougth long
    assert policy.get('checkout_duration', 0) > 3
    # now in UTC
    for now_str in [
        # winter time
        '2021-12-28 06:00:00', '2022-12-28 20:00:00',
        # winter to summer time
        '2022-03-22 06:00:00', '2022-03-22 20:00:00',
        # summer time
        '2022-06-28 05:00:00', '2022-06-28 19:00:00',
        # summer to winter time
        '2022-10-25 05:00:00', '2022-10-25 19:00:00'
    ]:
        with freeze_time(now_str, tz_offset=0):
            # get loan duration
            duration = get_default_loan_duration(loan, None)
            # now in datetime object
            now = datetime.now(timezone.utc)
            utc_end_date = now + duration
            # computed end date at the library timezone
            end_date = utc_end_date.astimezone(
                tz=lib_martigny.get_timezone())
            expected_utc_end_date = now + timedelta(
                days=policy['checkout_duration'])
            # expected end date at the library timezone
            expected_end_date = expected_utc_end_date.astimezone(
                lib_martigny.get_timezone())
            assert end_date.strftime('%Y-%m-%d') == \
                expected_end_date.strftime('%Y-%m-%d')
            assert end_date.hour == 23
            assert end_date.minute == 59

    # test library closed days
    now_str = '2022-02-04 14:00:00'
    with freeze_time(now_str, tz_offset=0):
        # get loan duration
        duration = get_default_loan_duration(loan, None)
        # now in datetime object
        now = datetime.now(timezone.utc)

        utc_end_date = now + duration
        # computed end date at the library timezone
        end_date = utc_end_date.astimezone(tz=lib_martigny.get_timezone())
        # saturday and sunday is closed (+2)
        expected_utc_end_date = now + timedelta(
            days=(policy['checkout_duration'] + 2))
        # expected end date at the library timezone
        expected_end_date = expected_utc_end_date.astimezone(
            lib_martigny.get_timezone())
        assert end_date.strftime('%Y-%m-%d') == \
            expected_end_date.strftime('%Y-%m-%d')
        assert end_date.hour == 23
        assert end_date.minute == 59
    item_lib_martigny.cancel_item_request(
        pid=loan.pid,
        transaction_location_pid=loc_public_martigny.pid,
        transaction_user_pid=librarian_martigny.pid
    )


def test_is_due_soon_is_late(
        item_on_loan_martigny_patron_and_loan_on_loan):
    """Test 'is due soon' and 'late' method about a loan."""
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

    # mock the sysdate to due_date + some seconds.
    mock_date = due_date + timedelta(seconds=2)
    with freeze_time(mock_date):
        assert loan.is_loan_late()


def test_loan_keep_and_to_anonymize(
        item_on_loan_martigny_patron_and_loan_on_loan,
        item2_on_loan_martigny_patron_and_loan_on_loan,
        librarian_martigny, loc_public_martigny):
    """Test anonymize and keep loan based on open transactions."""
    item, patron, loan = item_on_loan_martigny_patron_and_loan_on_loan
    assert not loan.is_concluded()
    assert not Loan.can_anonymize(loan_data=loan)

    params = {
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    item.checkin(**params)
    loan = Loan.get_record_by_pid(loan.pid)
    # CHECK #1 : loan concluded but patron doesn't request to anonymized loans.
    #  * item checked-in
    #  * no open events
    #  * patron doesn't specify any information into `keep_history`
    assert loan.is_concluded()
    assert not Loan.can_anonymize(loan_data=loan)

    # CHECK #2 : Update the patron 'keep_history'
    #   * patron should anonymize loans
    #   * as loan concluded date > 3 months, system need to keep reference and
    #     loan cannot be anonymized yet.
    #   TODO :: Adapt the value depending of the
    #           RERO_ILS_ANONYMISATION_MIN_TIME_LIMIT parameter
    patron.set_keep_history(False)
    loan = Loan.get_record_by_pid(loan.pid)
    assert loan.is_concluded()
    assert not Loan.can_anonymize(loan_data=loan)

    # CHECK #3 : Check if loan is concluded between 3 and 6 months.
    #   Between 3 and 6 months, the loan could be anonymized depending of
    #   patron setting. After 6 months, all loans are anonymized.
    #   TODO :: Adapt the value depending of the
    #           RERO_ILS_ANONYMISATION_MAX_TIME_LIMIT parameter
    four_months_ago = datetime.utcnow() - timedelta(days=4 * 31)
    loan['transaction_date'] = four_months_ago.isoformat()
    assert loan.is_concluded()
    assert loan.can_anonymize(loan_data=loan)

    # Update the loan to set the "to_anonymize" attribute into DB
    loan.update(loan, dbcommit=True, reindex=True)

    # test loans with fees
    #   Create a loan, update end_date to set this loan as overdue.
    #   Create notifications about this loan (overdue_loan_notification)
    #   This notification will create a new PatronTransaction with a fee.
    #   This will cause that this loan cannot be concluded and anonymize
    item, patron, loan = item2_on_loan_martigny_patron_and_loan_on_loan
    assert not loan.is_concluded()
    assert not Loan.can_anonymize(loan_data=loan)
    #  we update the loan end_date, removing 1 year. We are now sure that all
    #  possible library exceptions don't conflict with `library.open_days`
    #  computation
    end_date = datetime.now(timezone.utc) - timedelta(days=365)
    loan['end_date'] = end_date.isoformat()
    loan.update(loan, dbcommit=True, reindex=True)

    create_notifications(types=[
        NotificationType.DUE_SOON,
        NotificationType.OVERDUE
    ])
    flush_index(NotificationsSearch.Meta.index)
    flush_index(LoansSearch.Meta.index)

    params = {
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    item.checkin(**params)
    loan = Loan.get_record_by_pid(loan.pid)

    assert not loan.is_concluded()
    assert not Loan.can_anonymize(loan_data=loan)


def test_anonymizer_job(
        item_on_loan_martigny_patron_and_loan_on_loan,
        librarian_martigny, loc_public_martigny):
    """Test loan anonymizer job."""
    item, patron, loan = item_on_loan_martigny_patron_and_loan_on_loan

    # make the loan overdue and create related notifications
    loan_lib = Library.get_record_by_pid(loan.library_pid)
    add_days = 10
    open_days = []
    while len(open_days) < 10:
        end_date = datetime.now(timezone.utc) - timedelta(days=add_days)
        open_days = loan_lib.get_open_days(end_date)
        add_days += 1
    loan['end_date'] = end_date.isoformat()
    loan.update(loan, dbcommit=True, reindex=True)
    create_notifications(types=[
        NotificationType.DUE_SOON,
        NotificationType.OVERDUE
    ])
    flush_index(NotificationsSearch.Meta.index)
    flush_index(LoansSearch.Meta.index)

    # ensure than this loan cannot be anonymize (it's not yet concluded and
    # could have open fees [depending of the related CIPO])
    assert not loan.is_concluded()
    assert not Loan.can_anonymize(loan_data=loan)

    # update the patron `keep_history` setting to ensure the patron want keep
    # its history --> transaction concluded less than 6 months ago cannot be
    # anonymized.
    patron.set_keep_history(True)
    params = {
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    item.checkin(**params)
    loan = Loan.get_record_by_pid(loan.pid)
    # ensure than, after check-in, the loan isn't considerate as 'concluded'
    # (because of open fees transactions)
    assert not loan.is_concluded()

    # So a this time, if we run the `loan_anonymizer` task, none loan cannot
    # be anonymized --> return should be 0
    count = loan_anonymizer(dbcommit=True, reindex=True)
    assert count == 0

    # We will now update the loan `transaction_date` to 1 year ago and close
    # all open transactions about it.
    patron.set_keep_history(False)
    one_year_ago = datetime.now() - timedelta(days=365)
    loan['transaction_date'] = one_year_ago.isoformat()
    loan = loan.update(loan, dbcommit=True, reindex=True)
    # close open transactions and notifications
    for pid in get_transactions_pids_for_patron(patron.get('pid'), 'open'):
        transaction = PatronTransaction.get_record_by_pid(pid)
        transaction['status'] = 'closed'
        transaction.update(transaction, dbcommit=True, reindex=True)

    # ensure than, after these change, the loan can be anonymize.
    assert Loan.can_anonymize(loan_data=loan)

    # run the `loan_anonymizer` task and check the result. At least our loan
    # should be anonymize.
    count = len(list(Loan.get_anonymized_candidates()))
    msg = loan_anonymizer(dbcommit=True, reindex=True)
    assert msg == count


@mock.patch.object(Loan, 'can_anonymize', mock.MagicMock(return_value=False))
def test_anonymize_candidates(
    item2_on_loan_martigny_patron_and_loan_on_loan, patron_martigny,
    librarian_martigny, loc_public_martigny
):
    """Test loan anonymize candidates."""
    item, patron, loan = item2_on_loan_martigny_patron_and_loan_on_loan
    if item.status == ItemStatus.ON_SHELF:
        params = {
            'patron_pid': patron_martigny.pid,
            'transaction_location_pid': loc_public_martigny.pid,
            'transaction_user_pid': librarian_martigny.pid,
            'pickup_location_pid': loc_public_martigny.pid
        }
        item, actions = item.checkout(**params)
        loan = Loan.get_record_by_pid(actions[LoanAction.CHECKOUT].get('pid'))

    # The loan isn't concluded at this time, no candidates should be returned
    candidates = [loan.pid for loan in Loan.get_anonymized_candidates()]
    assert loan.pid not in candidates

    # Force the patron to keep history and conclude the loan.
    # Force the transaction date to 1 year ago. The loan should now be into
    # the anonymize candidate.
    patron.set_keep_history(True)
    params = {
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    item.checkin(**params)
    loan = Loan.get_record_by_pid(loan.pid)
    one_year_ago = datetime.now(timezone.utc) - timedelta(days=365)
    loan['transaction_date'] = one_year_ago.isoformat()
    loan = loan.update(loan, dbcommit=True, reindex=True)
    flush_index(LoansSearch.Meta.index)

    candidates = [loan.pid for loan in Loan.get_anonymized_candidates()]
    assert loan.pid in candidates

    # Set the transaction date to 4 months ago. As the patron want to keep
    # history, the loan isn't yet an anonymize candidate.
    four_month_ago = datetime.now(timezone.utc) - timedelta(days=4*30)
    loan['transaction_date'] = four_month_ago.isoformat()
    loan = loan.update(loan, dbcommit=True, reindex=True)
    flush_index(LoansSearch.Meta.index)

    candidates = [loan.pid for loan in Loan.get_anonymized_candidates()]
    assert loan.pid not in candidates

    # Now force the patron to not keep history setting. The loan is older than
    # 3 months, the loan must be an anonymize candidate.
    patron.set_keep_history(False)

    candidates = [loan.pid for loan in Loan.get_anonymized_candidates()]
    assert loan.pid in candidates


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


def test_request_expire_date(
    item_on_shelf_martigny_patron_and_loan_pending,
    librarian_martigny, loc_public_martigny, mailbox
):
    """Test request expiration date consistency."""
    item, patron, loan = item_on_shelf_martigny_patron_and_loan_pending
    assert item.status == ItemStatus.ON_SHELF

    # STEP#0 : UPDATE THE CIRCULATION POLICY
    #   Add setting to the corresponding circulation policy to allow request
    #   automatic expiration
    cipo = get_circ_policy(loan)

    original_cipo = deepcopy(cipo)
    cipo['allow_requests'] = True
    cipo['pickup_hold_duration'] = 44
    cipo = cipo.update(cipo, dbcommit=True, reindex=True)

    # STEP#1 : VALIDATE THE REQUEST
    #   When a request is validated, the item status becomes AT_DESK and the
    #   loan status becomes ITEM_AT_DESK. Additionally the request expiration
    #   date is specified into the loan information.
    params = {
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid,
        'pid': loan.pid
    }
    item, actions = item.validate_request(**params)
    loan = Loan.get_record_by_pid(loan.pid)
    assert item.status == ItemStatus.AT_DESK
    assert loan['state'] == LoanState.ITEM_AT_DESK
    assert 'request_expire_date' in loan
    assert 'request_start_date' in loan

    trans_date = ciso8601.parse_datetime(loan['transaction_date'])
    request_expire_date = ciso8601.parse_datetime(loan['request_expire_date'])
    open_days = (request_expire_date - trans_date).days
    assert open_days >= cipo['pickup_hold_duration']
    # NOTE : we check using '>=' because the exact day could be a closed day.
    request_start_date = ciso8601.parse_datetime(loan['request_start_date'])
    assert request_start_date.date() == datetime.today().date()

    # If we check about expired request now, no result should be found
    assert len(list(get_expired_request())) == 0

    # Check the notification :: check if the request expiration date is well
    # introduced into the body of availability notification message
    mailbox.clear()
    process_notifications(NotificationType.AVAILABILITY)
    assert len(mailbox)
    body = mailbox[-1].body
    assert request_expire_date.strftime('%d/%m/%Y') in body

    # ADDITIONAL TESTS ::
    #   A) test exception from loan indexer listener (this is more for code
    #      coverage than a real test).
    loan['item_pid']['value'] = 'dummy_pid'
    loan.update(loan, dbcommit=True, reindex=True)

    # RESET THE CIPO
    cipo.update(original_cipo, dbcommit=True, reindex=True)
