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
from datetime import datetime, timedelta, timezone

import pytest
from invenio_circulation.proxies import current_circulation
from invenio_circulation.search.api import LoansSearch
from utils import flush_index, get_mapping

from rero_ils.modules.loans.api import Loan, LoanState, get_loans_by_patron_pid
from rero_ils.modules.loans.tasks import loan_anonymizer
from rero_ils.modules.loans.utils import get_default_loan_duration
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

    assert get_default_loan_duration(new_loan, None) == timedelta(0)


@pytest.mark.skip(reason="In progress")
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

    patron['patron']['keep_history'] = False
    patron.update(patron, dbcommit=True, reindex=True)

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


@pytest.mark.skip(reason="In progress")
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

    patron['patron']['keep_history'] = True
    patron.update(patron, dbcommit=True, reindex=True)

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

    patron['patron']['keep_history'] = False
    patron.update(patron, dbcommit=True, reindex=True)
    # close open transactions and notifications
    for transaction in PatronTransaction.get_transactions_by_patron_pid(
                patron.get('pid'), 'open'):
        transaction = PatronTransaction.get_record_by_pid(transaction.pid)
        transaction['status'] = 'closed'
        transaction.update(transaction, dbcommit=True, reindex=True)
    msg = loan_anonymizer(dbcommit=True, reindex=True)
    assert msg == 'number_of_loans_anonymized: 2'
