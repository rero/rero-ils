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

"""Tests REST return an item API methods in the item api_views."""
from datetime import date, datetime, timedelta, timezone

from flask import url_for
from flask_babel import gettext as _
from invenio_accounts.testutils import login_user_via_session
from utils import get_json, postdata

from rero_ils.modules.items.api import Item
from rero_ils.modules.items.models import ItemStatus
from rero_ils.modules.loans.utils import get_circ_policy, sum_for_fees
from rero_ils.modules.patron_transactions.utils import \
    get_last_transaction_by_loan_pid


def test_checkin_an_item(
        client, librarian_martigny, lib_martigny,
        item_on_loan_martigny_patron_and_loan_on_loan, loc_public_martigny,
        item2_on_loan_martigny_patron_and_loan_on_loan,
        circulation_policies):
    """Test the frontend return a checked-out item action."""
    # test passes when all required parameters are given
    login_user_via_session(client, librarian_martigny.user)
    item, patron, loan = item_on_loan_martigny_patron_and_loan_on_loan

    # test fails when there is a missing required parameter
    res, data = postdata(
        client,
        'api_item.checkin',
        dict(
            item_pid=item.pid
        )
    )
    assert res.status_code == 400

    # test fails when there is a missing required parameter
    res, data = postdata(
        client,
        'api_item.checkin',
        dict(
            item_pid=item.pid,
            transaction_location_pid=loc_public_martigny.pid
        )
    )
    assert res.status_code == 400

    # test fails when there is a missing required parameter
    # when item record not found in database, api returns 404
    res, data = postdata(
        client,
        'api_item.checkin',
        dict(
            transaction_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny.pid
        )
    )
    assert res.status_code == 404

    # test passes when the transaction location pid is given
    res, data = postdata(
        client,
        'api_item.checkin',
        dict(
            item_pid=item.pid,
            transaction_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny.pid
        )
    )
    assert res.status_code == 200
    item = Item.get_record_by_pid(item.pid)
    assert item.status == ItemStatus.ON_SHELF

    # test passes when the transaction library pid is given
    item, patron, loan = item2_on_loan_martigny_patron_and_loan_on_loan
    res, data = postdata(
        client,
        'api_item.checkin',
        dict(
            item_pid=item.pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny.pid
        )
    )
    assert res.status_code == 200
    item = Item.get_record_by_pid(item.pid)
    assert item.status == ItemStatus.ON_SHELF


def test_auto_checkin_else(client, librarian_martigny,
                           patron_martigny, loc_public_martigny,
                           item_lib_martigny, json_header, lib_martigny,
                           loc_public_saxon):
    """Test item checkin no action."""
    login_user_via_session(client, librarian_martigny.user)
    res, data = postdata(
        client,
        'api_item.checkin',
        dict(
            item_pid=item_lib_martigny.pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny.pid
        )
    )
    assert res.status_code == 400
    assert get_json(res)['status'] == \
        _('error: No circulation action performed: on shelf')


def test_checkin_overdue_item(
        client, librarian_martigny, loc_public_martigny,
        item_on_loan_martigny_patron_and_loan_on_loan):
    """Test a checkin for an overdue item with incremental fees."""

    item, patron, loan = item_on_loan_martigny_patron_and_loan_on_loan

    # Update the circulation policy corresponding to the loan
    # Update the loan due date
    cipo = get_circ_policy(loan)
    cipo['overdue_fees'] = {
        'intervals': [
            {'from': 1, 'to': 5, 'fee_amount': 0.50},
            {'from': 6, 'to': 10, 'fee_amount': 1},
            {'from': 11, 'fee_amount': 2},
        ]
    }
    cipo.update(data=cipo, dbcommit=True, reindex=True)
    end = date.today() - timedelta(days=30)
    end = datetime(end.year, end.month, end.day, tzinfo=timezone.utc)
    end = end - timedelta(microseconds=1)
    loan['end_date'] = end.isoformat()
    loan = loan.update(loan, dbcommit=True, reindex=True)

    fees = loan.get_overdue_fees
    total_fees = sum_for_fees(fees)
    assert len(fees) > 0
    assert total_fees > 0

    # Check overdues preview API and check result
    url = url_for('api_loan.preview_loan_overdue', loan_pid=loan.pid)
    login_user_via_session(client, librarian_martigny.user)
    res = client.get(url)
    data = get_json(res)
    assert res.status_code == 200
    assert len(data['steps']) > 0
    assert data['total'] > 0

    url = url_for(
        'api_patrons.patron_overdue_preview_api',
        patron_pid=patron.pid
    )
    res = client.get(url)
    data = get_json(res)
    assert res.status_code == 200
    assert len(data) == 1
    assert data[0]['loan']['pid'] == loan.pid
    assert len(data[0]['fees']['steps']) > 0
    assert data[0]['fees']['total'] > 0

    # Do the checkin on the item
    res, data = postdata(
        client,
        'api_item.checkin',
        dict(
            item_pid=item.pid,
            transaction_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny.pid
        )
    )
    assert res.status_code == 200
    item = Item.get_record_by_pid(item.pid)
    assert item.status == ItemStatus.ON_SHELF

    # check if overdue transaction are created
    trans = get_last_transaction_by_loan_pid(loan.pid)
    assert trans.total_amount == total_fees
    events = list(trans.events)
    assert len(events) == 1
    assert len(events[0].get('steps', [])) == len(fees)

    # reset the cipo
    del cipo['overdue_fees']
    cipo.update(data=cipo, dbcommit=True, reindex=True)
