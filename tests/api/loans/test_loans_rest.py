# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2022 RERO
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

"""Tests REST API item_types."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone

import ciso8601
import pytz
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from invenio_circulation.api import get_loan_for_item
from invenio_circulation.search.api import LoansSearch
from utils import check_timezone_date, flush_index, get_json, postdata

from rero_ils.modules.items.api import Item
from rero_ils.modules.items.utils import item_pid_to_object
from rero_ils.modules.libraries.api import LibrariesSearch, Library
from rero_ils.modules.loans.api import Loan, get_due_soon_loans, \
    get_last_transaction_loc_for_item, get_overdue_loans
from rero_ils.modules.loans.models import LoanAction, LoanState
from rero_ils.modules.notifications.api import NotificationsSearch
from rero_ils.modules.notifications.dispatcher import Dispatcher
from rero_ils.modules.notifications.models import NotificationType
from rero_ils.modules.notifications.utils import number_of_notifications_sent
from rero_ils.modules.operation_logs.api import OperationLogsSearch


def test_loans_search(
    client, loan_pending_martigny, rero_json_header, librarian_martigny,
    yesterday
):
    """Test record retrieval."""
    login_user_via_session(client, librarian_martigny.user)
    loan = loan_pending_martigny
    original_loan = deepcopy(loan)

    # STEP#1 :: CHECK FACETS ARE PRESENT INTO SEARCH RESULT
    url = url_for('invenio_records_rest.loanid_list',
                  exclude_status=LoanState.ITEM_RETURNED)
    res = client.get(url, headers=rero_json_header)
    data = get_json(res)
    facet_keys = ['end_date', 'misc_status', 'owner_library', 'patron_type',
                  'pickup_library', 'request_expire_date', 'status',
                  'transaction_library']
    assert all(key in data['aggregations'] for key in facet_keys)
    assert data['hits']['total']['value'] == 1

    # STEP#2 :: REQUEST EXPIRED
    #   Update the loan to simulate that this request is now expired.
    params = {'misc_status': 'expired_request'}
    url = url_for('invenio_records_rest.loanid_list', **params)
    res = client.get(url, headers=rero_json_header)
    data = get_json(res)
    assert data['hits']['total']['value'] == 0

    loan['request_expire_date'] = yesterday.isoformat()
    loan.update(loan, dbcommit=True, reindex=True)
    res = client.get(url, headers=rero_json_header)
    data = get_json(res)
    assert data['hits']['total']['value'] == 1

    # STEP#3 :: LOAN IS OVERDUE
    #   Update the loan to be overdue and test the API search.
    params = {'misc_status': 'overdue'}
    url = url_for('invenio_records_rest.loanid_list', **params)
    res = client.get(url, headers=rero_json_header)
    data = get_json(res)
    assert data['hits']['total']['value'] == 0

    loan['end_date'] = yesterday.isoformat()
    loan.update(loan, dbcommit=True, reindex=True)
    res = client.get(url, headers=rero_json_header)
    data = get_json(res)
    assert data['hits']['total']['value'] == 1

    # RESET THE LOAN (for next tests)
    loan.update(original_loan, dbcommit=True, reindex=True)


def test_loan_access_permissions(client, librarian_martigny,
                                 loc_public_saxon,
                                 patron_martigny,
                                 item_lib_sion,
                                 item2_lib_sion,
                                 patron_sion_multiple,
                                 librarian_sion,
                                 patron_sion,
                                 patron2_martigny,
                                 circulation_policies,
                                 loan_pending_martigny,
                                 item_lib_martigny,
                                 loc_public_sion
                                 ):
    """Test loans read permissions."""
    # ensure we have loans from the two configured organisation.
    login_user_via_session(client, librarian_sion.user)
    res, _ = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item_lib_sion.pid,
            patron_pid=patron_sion.pid,
            transaction_location_pid=loc_public_saxon.pid,
            transaction_user_pid=librarian_martigny.pid,
        )
    )
    assert res.status_code == 200

    loan_pids = Loan.get_all_pids()
    loans = [Loan.get_record_by_pid(pid) for pid in loan_pids]
    loans_martigny = [
        loan for loan in loans if loan.organisation_pid == 'org1']
    loans_sion = [loan for loan in loans if loan.organisation_pid == 'org2']
    assert loans
    assert loan_pids
    assert loans_martigny
    assert loans_sion

    # test query filters with a user who is librarian and patron in org2 and
    # patron in org1
    login_user_via_session(client, librarian_sion.user)
    # create a loan for itself
    res, _ = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item2_lib_sion.pid,
            patron_pid=patron_sion_multiple.pid,
            transaction_location_pid=loc_public_sion.pid,
            transaction_user_pid=librarian_sion.pid,
        )
    )
    assert res.status_code == 200

    # act as multiple patron
    login_user_via_session(client, patron_sion_multiple.user)
    # without query filter I should have 3 loans one of mine and two
    # in my employed organisation, the other patron loan of my patron org
    # should be filtered
    loan_list = url_for(
        'invenio_records_rest.loanid_list',
        q=f'')
    res = client.get(loan_list)
    assert res.status_code == 200
    data = get_json(res)
    assert len(data['hits']['hits']) == 3

    # see only my loan
    loan_list = url_for(
        'invenio_records_rest.loanid_list',
        q=f'patron_pid:{patron_sion_multiple.pid}')
    res = client.get(loan_list)
    assert res.status_code == 200
    data = get_json(res)
    assert len(data['hits']['hits']) == 1

    # checkin the item to put it back to it's original state
    login_user_via_session(client, librarian_sion.user)

    res, data = postdata(
        client,
        'api_item.checkin',
        dict(
            item_pid=item2_lib_sion.pid,
            transaction_location_pid=loc_public_sion.pid,
            transaction_user_pid=librarian_sion.pid,
        )
    )
    assert res.status_code == 200

    res, _ = postdata(
        client,
        'api_item.checkin',
        dict(
            item_pid=item_lib_sion.pid,
            transaction_location_pid=loc_public_saxon.pid,
            transaction_user_pid=librarian_martigny.pid,
        )
    )
    assert res.status_code == 200


def test_due_soon_loans(client, librarian_martigny,
                        lib_martigny_data, lib_martigny,
                        patron_martigny, loc_public_martigny,
                        item_type_standard_martigny,
                        item_lib_martigny,
                        circ_policy_short_martigny, yesterday):
    """Test overdue loans."""
    login_user_via_session(client, librarian_martigny.user)
    item = item_lib_martigny
    item_pid = item.pid
    patron_pid = patron_martigny.pid
    can, reasons = item.can_delete
    assert can
    assert reasons == {}
    assert item.is_available()
    assert not get_last_transaction_loc_for_item(item_pid)
    assert not item.patron_has_an_active_loan_on_item(patron_martigny)

    from rero_ils.modules.circ_policies.api import CircPolicy
    circ_policy = CircPolicy.provide_circ_policy(
        item.organisation_pid,
        item.library_pid,
        patron_martigny.patron_type_pid,
        item.item_type_pid
    )
    circ_policy['reminders'][0]['days_delay'] = 7
    circ_policy['checkout_duration'] = 3
    circ_policy.update(circ_policy, dbcommit=True, reindex=True)

    # Remove library exception date to ensure to not been annoyed by
    # closed dates.
    custom_lib_data = deepcopy(lib_martigny_data)
    custom_lib_data['exception_dates'] = []
    lib_martigny.update(custom_lib_data, dbcommit=True, reindex=True)
    flush_index(LibrariesSearch.Meta.index)

    # checkout
    res, data = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item_pid,
            patron_pid=patron_pid,
            transaction_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny.pid,
        )
    )
    assert res.status_code == 200
    loan_pid = data.get('action_applied')[LoanAction.CHECKOUT].get('pid')
    # To be considered as 'due_soon', we need to update the loan start date
    # to figure than start_date occurs before due_date.
    loan = Loan.get_record_by_pid(loan_pid)
    start_date = ciso8601.parse_datetime(loan.get('start_date'))
    loan['start_date'] = (start_date - timedelta(days=30)).isoformat()
    loan.update(loan, dbcommit=True, reindex=True)

    due_soon_loans = list(get_due_soon_loans())
    assert due_soon_loans[0].get('pid') == loan_pid

    # test due date regarding multiple timezones
    checkout_loan = Loan.get_record_by_pid(loan_pid)
    loan_date = ciso8601.parse_datetime(checkout_loan.get('end_date'))

    # as instance timezone is Europe/Zurich, it should be either 21 or 22
    check_timezone_date(pytz.utc, loan_date, [21, 22])

    # should be 14:59/15:59 in US/Pacific (because of daylight saving time)
    check_timezone_date(pytz.timezone('US/Pacific'), loan_date, [14, 15])
    check_timezone_date(pytz.timezone('Europe/Amsterdam'), loan_date)

    # checkin the item to put it back to it's original state
    res, _ = postdata(
        client,
        'api_item.checkin',
        dict(
            item_pid=item_pid,
            pid=loan_pid,
            transaction_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny.pid
        )
    )
    assert res.status_code == 200

    # reset lib
    lib_martigny.update(lib_martigny_data, dbcommit=True, reindex=True)


def test_overdue_loans(client, librarian_martigny,
                       patron_martigny, loc_public_martigny,
                       item_type_standard_martigny,
                       item_lib_martigny, item2_lib_martigny,
                       patron_type_children_martigny,
                       circ_policy_short_martigny,
                       patron3_martigny_blocked):
    """Test overdue loans."""
    login_user_via_session(client, librarian_martigny.user)
    item = item_lib_martigny
    item_pid = item.pid
    patron_pid = patron_martigny.pid

    # checkout
    res, data = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item_pid,
            patron_pid=patron_pid,
            transaction_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny.pid,
        )
    )
    assert res.status_code == 200, "It probably failed while \
        test_due_soon_loans fail"

    loan_pid = data.get('action_applied')[LoanAction.CHECKOUT].get('pid')
    loan = Loan.get_record_by_pid(loan_pid)
    end_date = datetime.now(timezone.utc) - timedelta(days=7)
    loan['end_date'] = end_date.isoformat()
    loan.update(
        loan,
        dbcommit=True,
        reindex=True
    )

    overdue_loans = list(get_overdue_loans(patron_pid=patron_pid))
    assert overdue_loans[0].get('pid') == loan_pid
    assert number_of_notifications_sent(loan) == 0

    notification = loan.create_notification(
        _type=NotificationType.OVERDUE).pop()
    Dispatcher.dispatch_notifications([notification.get('pid')])
    flush_index(NotificationsSearch.Meta.index)
    flush_index(LoansSearch.Meta.index)
    flush_index(OperationLogsSearch.Meta.index)
    assert number_of_notifications_sent(loan) == 1
    # Check notification is created on operation logs
    assert len(list(
        OperationLogsSearch()
        .get_logs_by_notification_pid(notification.get('pid')))) == 1

    # Try a checkout for a blocked user :: It should be blocked
    res, data = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item2_lib_martigny.pid,
            patron_pid=patron3_martigny_blocked.pid,
            transaction_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny.pid,
        )
    )
    assert res.status_code == 403
    assert 'This patron is currently blocked' in data['message']

    # checkin the item to put it back to it's original state
    res, _ = postdata(
        client,
        'api_item.checkin',
        dict(
            item_pid=item_pid,
            pid=loan_pid,
            transaction_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny.pid,
        )
    )
    assert res.status_code == 200


def test_last_end_date_loans(client, librarian_martigny,
                             patron_martigny, loc_public_martigny,
                             item_lib_martigny,
                             circ_policy_short_martigny):
    """Test last_end_date of loan."""
    login_user_via_session(client, librarian_martigny.user)
    item = item_lib_martigny
    item_pid = item.pid
    patron_pid = patron_martigny.pid

    # checkout the item
    res, data = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item_pid,
            patron_pid=patron_pid,
            transaction_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny.pid,
        )
    )
    assert res.status_code == 200

    loan_pid = data.get('action_applied')[LoanAction.CHECKOUT].get('pid')
    loan = Loan.get_record_by_pid(loan_pid)
    assert loan['end_date'] == loan['last_end_date']

    end_date = loan['end_date']

    # checkin the item
    res, _ = postdata(
        client,
        'api_item.checkin',
        dict(
            item_pid=item_pid,
            pid=loan_pid,
            transaction_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny.pid,
        )
    )
    assert res.status_code == 200

    loan = Loan.get_record_by_pid(loan_pid)
    # check last_end_date is the last end_date
    assert loan['last_end_date'] == end_date
    # check end_date is equal to transaction_date
    assert loan['end_date'] == loan['transaction_date']


def test_checkout_item_transit(client, mailbox, item2_lib_martigny,
                               librarian_martigny,
                               librarian_saxon,
                               patron_martigny,
                               loc_public_saxon, lib_martigny,
                               loc_public_martigny,
                               circulation_policies):
    """Test checkout of an item in transit."""
    assert item2_lib_martigny.is_available()
    mailbox.clear()

    # request
    login_user_via_session(client, librarian_martigny.user)
    loc_public_martigny['notification_email'] = 'dummy_email@fake.domain'
    loc_public_martigny['send_notification'] = True
    loc_public_martigny.update(
        loc_public_martigny.dumps(),
        dbcommit=True,
        reindex=True
    )

    res, data = postdata(
        client,
        'api_item.librarian_request',
        dict(
            item_pid=item2_lib_martigny.pid,
            pickup_location_pid=loc_public_saxon.pid,
            patron_pid=patron_martigny.pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny.pid
        )
    )
    assert res.status_code == 200
    actions = data.get('action_applied')
    loan_pid = actions[LoanAction.REQUEST].get('pid')
    assert not item2_lib_martigny.is_available()

    assert len(mailbox) == 1
    assert mailbox[-1].recipients == [
        loc_public_martigny['notification_email']]

    loan = Loan.get_record_by_pid(loan_pid)
    assert loan['state'] == LoanState.PENDING

    # reset the location
    del loc_public_martigny['notification_email']
    del loc_public_martigny['send_notification']
    loc_public_martigny.update(
        loc_public_martigny.dumps(),
        dbcommit=True,
        reindex=True
    )

    # validate request
    res, _ = postdata(
        client,
        'api_item.validate_request',
        dict(
            item_pid=item2_lib_martigny.pid,
            pid=loan_pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny.pid
        )
    )
    assert res.status_code == 200
    assert not item2_lib_martigny.is_available()
    item = Item.get_record_by_pid(item2_lib_martigny.pid)
    assert not item.is_available()

    loan = Loan.get_record_by_pid(loan_pid)
    assert loan['state'] == LoanState.ITEM_IN_TRANSIT_FOR_PICKUP

    login_user_via_session(client, librarian_saxon.user)
    # receive
    res, _ = postdata(
        client,
        'api_item.receive',
        dict(
            item_pid=item2_lib_martigny.pid,
            pid=loan_pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny.pid
        )
    )
    assert res.status_code == 200
    assert not item2_lib_martigny.is_available()
    item = Item.get_record_by_pid(item2_lib_martigny.pid)
    assert not item.is_available()

    loan_before_checkout = get_loan_for_item(item_pid_to_object(item.pid))
    assert loan_before_checkout.get('state') == LoanState.ITEM_AT_DESK
    # checkout
    res, _ = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item2_lib_martigny.pid,
            patron_pid=patron_martigny.pid,
            transaction_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny.pid,
        )
    )
    assert res.status_code == 200
    item = Item.get_record_by_pid(item2_lib_martigny.pid)
    loan_after_checkout = get_loan_for_item(item_pid_to_object(item.pid))
    assert loan_after_checkout.get('state') == LoanState.ITEM_ON_LOAN
    assert loan_before_checkout.get('pid') == loan_after_checkout.get('pid')


def test_timezone_due_date(client, librarian_martigny,
                           patron_martigny, loc_public_martigny,
                           item_type_standard_martigny,
                           item3_lib_martigny,
                           circ_policy_short_martigny,
                           lib_martigny):
    """Test that timezone affects due date regarding library location."""

    # Close the library all days. Except Monday.
    del lib_martigny['exception_dates']
    lib_martigny['opening_hours'] = [
        {
            "day": "monday",
            "is_open": True,
            "times": [
                {
                    "start_time": "07:00",
                    "end_time": "19:00"
                }
            ]
        },
        {
            "day": "tuesday",
            "is_open": False,
            "times": []
        },
        {
            "day": "wednesday",
            "is_open": False,
            "times": []
        },
        {
            "day": "thursday",
            "is_open": False,
            "times": []
        },
        {
            "day": "friday",
            "is_open": False,
            "times": []
        },
        {
            "day": "saturday",
            "is_open": False,
            "times": []
        },
        {
            "day": "sunday",
            "is_open": False,
            "times": []
        }
    ]
    lib_martigny.update(lib_martigny, dbcommit=True, reindex=True)

    # Change circulation policy
    checkout_duration = 3
    item = item3_lib_martigny
    item_pid = item.pid
    patron_pid = patron_martigny.pid
    from rero_ils.modules.circ_policies.api import CircPolicy
    circ_policy = CircPolicy.provide_circ_policy(
        item.organisation_pid,
        item.library_pid,
        patron_martigny.patron_type_pid,
        item.item_type_pid
    )
    circ_policy['reminders'][0]['days_delay'] = 7
    circ_policy['checkout_duration'] = checkout_duration
    circ_policy.update(
        circ_policy,
        dbcommit=True,
        reindex=True
    )
    # Login to perform action
    login_user_via_session(client, librarian_martigny.user)

    # Checkout the item
    res, data = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item_pid,
            patron_pid=patron_pid,
            transaction_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny.pid,
        )
    )
    assert res.status_code == 200

    # Get Loan date (should be in UTC)
    loan_pid = data.get('action_applied')[LoanAction.CHECKOUT].get('pid')
    loan = Loan.get_record_by_pid(loan_pid)
    loan_end_date = loan.get('end_date')

    # Get next library open date (should be next monday after X-1 days) where
    # X is checkout_duration
    soon = datetime.now(pytz.utc) + timedelta(days=(checkout_duration-1))
    lib = Library.get_record_by_pid(item.library_pid)
    lib_datetime = lib.next_open(soon)

    # Loan date should be in UTC (as lib_datetime).
    loan_datetime = ciso8601.parse_datetime(loan_end_date)

    # Compare year, month and date for Loan due date: should be the same!
    fail_msg = "Check timezone for Loan and Library. \
It should be the same date, even if timezone changed."
    assert loan_datetime.year == lib_datetime.year, fail_msg
    assert loan_datetime.month == lib_datetime.month, fail_msg
    assert loan_datetime.day == lib_datetime.day, fail_msg
    # Loan date differs regarding timezone, and day of the year (GMT+1/2).
    check_timezone_date(pytz.utc, loan_datetime, [21, 22])


def test_librarian_request_on_blocked_user(
        client, item_lib_martigny, lib_martigny,
        librarian_martigny, loc_public_martigny,
        patron3_martigny_blocked,
        circulation_policies):
    """Librarian request on blocked user returns a specific 403 message."""
    assert item_lib_martigny.is_available()

    # request
    login_user_via_session(client, librarian_martigny.user)
    res, data = postdata(
        client,
        'api_item.librarian_request',
        dict(
            item_pid=item_lib_martigny.pid,
            patron_pid=patron3_martigny_blocked.pid,
            pickup_location_pid=loc_public_martigny.pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny.pid
        )
    )
    assert res.status_code == 403
    data = get_json(res)
    assert 'blocked' in data.get('message')
