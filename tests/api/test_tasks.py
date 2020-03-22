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

"""Tasks tests."""

from datetime import datetime, timedelta, timezone

from invenio_accounts.testutils import login_user_via_session
from utils import postdata

from rero_ils.modules.loans.api import Loan, LoanAction, LoansSearch, \
    get_due_soon_loans, get_overdue_loans
from rero_ils.modules.notifications.api import NotificationsSearch, \
    number_of_reminders_sent
from rero_ils.modules.notifications.tasks import \
    create_over_and_due_soon_notifications


def test_create_over_and_due_soon_notifications_task(
        client, librarian_martigny_no_email, patron_martigny_no_email,
        item_lib_martigny, circ_policy_short_martigny,
        loc_public_martigny, lib_martigny):
    """Test overdue and due_soon loans."""
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

    # test due_soon notification
    end_date = datetime.now(timezone.utc) + timedelta(days=3)
    loan['end_date'] = end_date.isoformat()
    loan.update(loan, dbcommit=True, reindex=True)

    due_soon_loans = get_due_soon_loans()

    assert due_soon_loans[0].get('pid') == loan_pid

    create_over_and_due_soon_notifications()
    NotificationsSearch.flush()
    LoansSearch.flush()

    assert loan.is_notified(notification_type='due_soon')

    # test overdue notification
    end_date = datetime.now(timezone.utc) - timedelta(days=7)
    loan['end_date'] = end_date.isoformat()
    loan.update(loan, dbcommit=True, reindex=True)

    overdue_loans = get_overdue_loans()
    assert overdue_loans[0].get('pid') == loan_pid

    create_over_and_due_soon_notifications()
    NotificationsSearch.flush()
    LoansSearch.flush()

    assert loan.is_notified(notification_type='overdue')
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
