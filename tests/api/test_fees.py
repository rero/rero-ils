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

"""Tests REST API notifications."""

import json
from datetime import datetime, timedelta, timezone

from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from invenio_circulation.search.api import LoansSearch
from utils import flush_index, get_json, to_relative_url

from rero_ils.modules.loans.api import Loan, LoanAction, get_overdue_loans
from rero_ils.modules.notifications.api import NotificationsSearch
from rero_ils.modules.organisations.api import Organisation


def test_create_fee(client, librarian_martigny_no_email,
                    librarian_sion_no_email,
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

    notification = loan.create_notification(notification_type='overdue')
    flush_index(NotificationsSearch.Meta.index)
    flush_index(LoansSearch.Meta.index)

    fee = list(notification.fees)[0]
    assert fee.get('amount') == 2
    assert fee.get('currency') == 'CHF'

    fee_url = url_for('invenio_records_rest.fee_item', pid_value=fee.pid)

    res = client.get(fee_url)
    assert res.status_code == 200

    login_user_via_session(client, librarian_sion_no_email.user)

    res = client.get(fee_url)
    assert res.status_code == 403


def test_create_fee_euro(client, librarian_martigny_no_email,
                         item_lib_martigny, patron_martigny_no_email):
    """ Test overdue loans with if we change the organisation default
        currency."""
    login_user_via_session(client, librarian_martigny_no_email.user)

    # create a checkout
    res = client.post(
        url_for('api_item.checkout'),
        data=json.dumps({
            'item_pid': item_lib_martigny.pid,
            'patron_pid': patron_martigny_no_email.pid
        }),
        content_type='application/json',
    )
    assert res.status_code == 200

    # load the created loan and place it in overdue
    data = get_json(res)
    loan_pid = data.get('action_applied')[LoanAction.CHECKOUT].get('pid')
    loan = Loan.get_record_by_pid(loan_pid)
    end_date = datetime.now(timezone.utc) - timedelta(days=7)
    loan['end_date'] = end_date.isoformat()
    loan.update(loan, dbcommit=True, reindex=True)
    overdue_loans = get_overdue_loans()
    assert overdue_loans[0].get('pid') == loan_pid

    # ensure that 'default_currency' of the linked organisation in 'EUR'
    org = Organisation.get_record_by_pid(loan.organisation_pid)
    org['default_currency'] = 'EUR'
    org.update(org, dbcommit=True, reindex=True)
    org = Organisation.get_record_by_pid(loan.organisation_pid)
    assert org.get('default_currency') == 'EUR'

    # create notification and check the created fee is in euro
    notification = loan.create_notification(notification_type='overdue')
    flush_index(NotificationsSearch.Meta.index)
    flush_index(LoansSearch.Meta.index)
    fee = list(notification.fees)[0]
    assert fee.get('currency') == org.get('default_currency')
