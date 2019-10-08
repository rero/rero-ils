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

"""Tests REST API item_types."""

from copy import deepcopy
from datetime import datetime, timedelta, timezone

import ciso8601
import pytest
import pytz
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from invenio_circulation.api import get_loan_for_item
from invenio_circulation.search.api import LoansSearch
from utils import flush_index, postdata

from rero_ils.modules.items.api import Item
from rero_ils.modules.loans.api import Loan, LoanAction, get_due_soon_loans, \
    get_last_transaction_loc_for_item, get_loans_by_patron_pid, \
    get_overdue_loans
from rero_ils.modules.loans.utils import can_be_requested
from rero_ils.modules.notifications.api import Notification, \
    NotificationsSearch, number_of_reminders_sent


def test_loans_permissions(client, loan_pending_martigny, json_header):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.loanid_item', pid_value='1')

    res = client.get(item_url)
    assert res.status_code == 401

    res, _ = postdata(
        client,
        'invenio_records_rest.loanid_list',
        {}
    )
    assert res.status_code == 401

    res = client.put(
        url_for('invenio_records_rest.loanid_item', pid_value='1'),
        data={},
        headers=json_header
    )

    res = client.delete(item_url)
    assert res.status_code == 401


def test_loans_logged_permissions(client, loan_pending_martigny,
                                  librarian_martigny_no_email,
                                  json_header):
    """Test record retrieval."""
    login_user_via_session(client, librarian_martigny_no_email.user)
    item_url = url_for('invenio_records_rest.loanid_item', pid_value='1')

    res = client.get(item_url)
    assert res.status_code == 403

    res, _ = postdata(
        client,
        'invenio_records_rest.loanid_list',
        {}
    )
    assert res.status_code == 403

    res = client.put(
        url_for('invenio_records_rest.loanid_item', pid_value='1'),
        data={},
        headers=json_header
    )

    res = client.delete(item_url)
    assert res.status_code == 403


def test_loan_utils(client, patron_martigny_no_email,
                    patron2_martigny_no_email, circulation_policies,
                    loan_pending_martigny, item_lib_martigny):
    """Test loan utils."""
    loan = {
        'item_pid': item_lib_martigny.pid,
        'patron_pid': patron_martigny_no_email.pid
    }
    assert can_be_requested(loan)

    del loan['item_pid']
    with pytest.raises(Exception):
        assert can_be_requested(loan)

    assert loan_pending_martigny.patron_pid == patron2_martigny_no_email.pid
    assert not loan_pending_martigny.is_active

    with pytest.raises(TypeError):
        assert get_loans_by_patron_pid()
    assert get_loans_by_patron_pid(patron2_martigny_no_email.pid)

    with pytest.raises(TypeError):
        assert get_last_transaction_loc_for_item()

    assert loan_pending_martigny.organisation_pid

    new_loan = deepcopy(loan_pending_martigny)
    assert new_loan.organisation_pid
    del new_loan['item_pid']
    assert not new_loan.organisation_pid


def test_due_soon_loans(client, librarian_martigny_no_email,
                        patron_martigny_no_email, loc_public_martigny,
                        item_type_standard_martigny,
                        item_lib_martigny, json_header,
                        circ_policy_short_martigny):
    """Test overdue loans."""
    login_user_via_session(client, librarian_martigny_no_email.user)
    item = item_lib_martigny
    item_pid = item.pid
    patron_pid = patron_martigny_no_email.pid

    assert not item.is_loaned_to_patron(patron_martigny_no_email.get(
        'barcode'))
    assert item.can_delete
    assert item.available

    from rero_ils.modules.circ_policies.api import CircPolicy
    circ_policy = CircPolicy.provide_circ_policy(
        item.library_pid,
        patron_martigny_no_email.patron_type_pid,
        item.item_type_pid
    )
    circ_policy['number_of_days_before_due_date'] = 7
    circ_policy['checkout_duration'] = 3
    circ_policy.update(
        circ_policy,
        dbcommit=True,
        reindex=True
    )

    # checkout
    res, data = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item_pid,
            patron_pid=patron_pid
        )
    )
    assert res.status_code == 200
    loan_pid = data.get('action_applied')[LoanAction.CHECKOUT].get('pid')
    due_soon_loans = get_due_soon_loans()
    assert due_soon_loans[0].get('pid') == loan_pid

    # test due date hour
    checkout_loan = Loan.get_record_by_pid(loan_pid)

    end_date = ciso8601.parse_datetime(
        checkout_loan.get('end_date'))
    assert end_date.minute == 59 and end_date.hour == 23

    new_timezone = pytz.timezone('US/Pacific')
    end_date = ciso8601.parse_datetime(
        checkout_loan.get('end_date')).astimezone(new_timezone)
    assert end_date.minute == 59 and end_date.hour != 23

    new_timezone = pytz.timezone('Europe/Amsterdam')
    end_date = ciso8601.parse_datetime(
        checkout_loan.get('end_date')).astimezone(new_timezone)
    assert end_date.minute == 59 and end_date.hour != 23

    # checkin the item to put it back to it's original state
    res, _ = postdata(
        client,
        'api_item.checkin',
        dict(
            item_pid=item_pid,
            pid=loan_pid
        )
    )
    assert res.status_code == 200


def test_overdue_loans(client, librarian_martigny_no_email,
                       patron_martigny_no_email, loc_public_martigny,
                       item_type_standard_martigny,
                       item_lib_martigny, json_header,
                       circ_policy_short_martigny):
    """Test overdue loans."""
    login_user_via_session(client, librarian_martigny_no_email.user)
    item = item_lib_martigny
    item_pid = item.pid
    patron_pid = patron_martigny_no_email.pid

    # checkout
    res, data = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item_pid,
            patron_pid=patron_pid
        )
    )
    assert res.status_code == 200

    loan_pid = data.get('action_applied')[LoanAction.CHECKOUT].get('pid')
    loan = Loan.get_record_by_pid(loan_pid)
    end_date = datetime.now(timezone.utc) - timedelta(days=7)
    loan['end_date'] = end_date.isoformat()
    loan.update(
        loan,
        dbcommit=True,
        reindex=True
    )

    overdue_loans = get_overdue_loans()
    assert overdue_loans[0].get('pid') == loan_pid

    assert number_of_reminders_sent(loan) == 0

    loan.create_notification(notification_type='overdue')
    flush_index(NotificationsSearch.Meta.index)
    flush_index(LoansSearch.Meta.index)

    assert number_of_reminders_sent(loan) == 1

    # checkin the item to put it back to it's original state
    res, _ = postdata(
        client,
        'api_item.checkin',
        dict(
            item_pid=item_pid,
            pid=loan_pid
        )
    )
    assert res.status_code == 200


def test_checkout_item_transit(client, item2_lib_martigny,
                               librarian_martigny_no_email,
                               librarian_saxon_no_email,
                               patron_martigny_no_email,
                               loc_public_saxon,
                               circulation_policies):
    """Test checkout of an item in transit."""
    assert item2_lib_martigny.available

    # request
    login_user_via_session(client, librarian_martigny_no_email.user)

    res, data = postdata(
        client,
        'api_item.librarian_request',
        dict(
            item_pid=item2_lib_martigny.pid,
            pickup_location_pid=loc_public_saxon.pid,
            patron_pid=patron_martigny_no_email.pid
        )
    )
    assert res.status_code == 200
    actions = data.get('action_applied')
    loan_pid = actions[LoanAction.REQUEST].get('pid')
    assert not item2_lib_martigny.available

    loan = Loan.get_record_by_pid(loan_pid)
    assert loan.get('state') == 'PENDING'

    # validate request
    res, _ = postdata(
        client,
        'api_item.validate_request',
        dict(
            item_pid=item2_lib_martigny.pid,
            pid=loan_pid
        )
    )
    assert res.status_code == 200
    assert not item2_lib_martigny.available
    item = Item.get_record_by_pid(item2_lib_martigny.pid)
    assert not item.available

    loan = Loan.get_record_by_pid(loan_pid)
    assert loan.get('state') == 'ITEM_IN_TRANSIT_FOR_PICKUP'

    login_user_via_session(client, librarian_saxon_no_email.user)
    # receive
    res, _ = postdata(
        client,
        'api_item.receive',
        dict(
            item_pid=item2_lib_martigny.pid,
            pid=loan_pid
        )
    )
    assert res.status_code == 200
    assert not item2_lib_martigny.available
    item = Item.get_record_by_pid(item2_lib_martigny.pid)
    assert not item.available

    loan_before_checkout = get_loan_for_item(item.pid)
    assert loan_before_checkout.get('state') == 'ITEM_AT_DESK'
    # checkout
    res, _ = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item2_lib_martigny.pid,
            patron_pid=patron_martigny_no_email.pid
        )
    )
    assert res.status_code == 200
    item = Item.get_record_by_pid(item2_lib_martigny.pid)
    loan_after_checkout = get_loan_for_item(item.pid)
    assert loan_after_checkout.get('state') == 'ITEM_ON_LOAN'
    assert loan_before_checkout.get('pid') == loan_after_checkout.get('pid')
