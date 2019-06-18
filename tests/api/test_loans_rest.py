#
# This file is part of RERO ILS.
# Copyright (C) 2017 RERO.
#
# RERO ILS is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# RERO ILS is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RERO ILS; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Tests REST API item_types."""

import json
from copy import deepcopy
from datetime import datetime, timedelta, timezone

import pytest
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from invenio_circulation.search.api import LoansSearch
from utils import flush_index, get_json

from rero_ils.modules.loans.api import Loan, LoanAction, get_due_soon_loans, \
    get_last_transaction_loc_for_item, get_loans_by_patron_pid, \
    get_overdue_loans
from rero_ils.modules.loans.utils import can_be_requested
from rero_ils.modules.notifications.api import Notification, \
    NotificationsSearch, number_of_reminders_sent


def test_loans_permissions(client, loan_pending_martigny, json_header):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.loanid_item', pid_value='1')
    post_url = url_for('invenio_records_rest.loanid_list')

    res = client.get(item_url)
    assert res.status_code == 401

    res = client.post(
        post_url,
        data={},
        headers=json_header
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
    post_url = url_for('invenio_records_rest.loanid_list')

    res = client.get(item_url)
    assert res.status_code == 403

    res = client.post(
        post_url,
        data={},
        headers=json_header
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
    res = client.post(
        url_for('api_item.checkout'),
        data=json.dumps(
            dict(
                item_pid=item_pid,
                patron_pid=patron_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200
    data = get_json(res)
    loan_pid = data.get('action_applied')[LoanAction.CHECKOUT].get('loan_pid')
    due_soon_loans = get_due_soon_loans()
    assert due_soon_loans[0].get('loan_pid') == loan_pid

    # checkin the item to put it back to it's original state
    res = client.post(
        url_for('api_item.checkin'),
        data=json.dumps(
            dict(
                item_pid=item_pid,
                loan_pid=loan_pid
            )
        ),
        content_type='application/json',
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
    res = client.post(
        url_for('api_item.checkout'),
        data=json.dumps(
            dict(
                item_pid=item_pid,
                patron_pid=patron_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200

    data = get_json(res)
    loan_pid = data.get('action_applied')[LoanAction.CHECKOUT].get('loan_pid')
    loan = Loan.get_record_by_pid(loan_pid)
    end_date = datetime.now(timezone.utc) - timedelta(days=7)
    loan['end_date'] = end_date.isoformat()
    loan.update(
        loan,
        dbcommit=True,
        reindex=True
    )

    overdue_loans = get_overdue_loans()
    assert overdue_loans[0].get('loan_pid') == loan_pid

    assert number_of_reminders_sent(loan) == 0

    loan.create_notification(notification_type='overdue')
    flush_index(NotificationsSearch.Meta.index)
    flush_index(LoansSearch.Meta.index)

    assert number_of_reminders_sent(loan) == 1

    # checkin the item to put it back to it's original state
    res = client.post(
        url_for('api_item.checkin'),
        data=json.dumps(
            dict(
                item_pid=item_pid,
                loan_pid=loan_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200
