# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2020 RERO
# Copyright (C) 2020 UCLouvain
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

"""Tests Selfcheck api."""

from __future__ import absolute_import, print_function

from datetime import datetime, timedelta, timezone

import pytest
from invenio_accounts.testutils import login_user_via_session
from invenio_circulation.search.api import LoansSearch
from utils import flush_index, postdata

from rero_ils.modules.loans.api import Loan, LoanAction, LoanState
from rero_ils.modules.notifications.api import NotificationsSearch, \
    number_of_reminders_sent
from rero_ils.modules.selfcheck.api import authorize_patron, enable_patron, \
    item_information, patron_information, selfcheck_checkin, \
    selfcheck_checkout, selfcheck_login, system_status, \
    validate_patron_account
from rero_ils.modules.selfcheck.utils import check_sip2_module

# skip tests if invenio-sip2 module is not installed
pytestmark = pytest.mark.skipif(not check_sip2_module(),
                                reason='invenio-sip2 not installed')


def test_invenio_sip2():
    """Test invenio-sip2 module install."""
    assert check_sip2_module()


def test_selfcheck_login(sip2_librarian_martigny_no_email):
    """Test selfcheck client login."""

    # test failed login
    response = selfcheck_login('invalid_user',
                               'invalid_password')
    assert not response

    # test success login
    response = selfcheck_login(
        sip2_librarian_martigny_no_email.get('email'),
        sip2_librarian_martigny_no_email.get('birth_date'))
    assert response
    assert response.get('authenticated')


def test_authorize_patron(sip2_patron_martigny_no_email):
    """Test authorize patron."""

    # try to authorize with wrong password
    response = authorize_patron(sip2_patron_martigny_no_email.get(
        'patron', {}).get('barcode'), 'invalid_password')
    assert not response

    # try to authorize with wrong barcode
    response = authorize_patron('invalid_barcode', 'invalid_password')
    assert not response

    # authorize success
    response = authorize_patron(
        sip2_patron_martigny_no_email.get('patron', {}).get('barcode'),
        sip2_patron_martigny_no_email.get('birth_date'))
    assert response


def test_validate_patron(patron_martigny):
    """Test validate patron."""
    # test valid patron barcode
    assert validate_patron_account(
        patron_martigny.get('patron', {}).get('barcode'))

    # test invalid patron barcode
    assert not validate_patron_account('invalid_barcode')


def test_system_status(sip2_librarian_martigny_no_email):
    """Test automated circulation system status."""
    response = system_status(sip2_librarian_martigny_no_email.get('pid'))
    assert response.get('institution_id') == \
        sip2_librarian_martigny_no_email.library_pid


def test_enable_patron(sip2_patron_martigny_no_email):
    """Test enable patron."""
    response = enable_patron(
        sip2_patron_martigny_no_email.get('patron', {}).get('barcode'))
    assert response['institution_id'] == sip2_patron_martigny_no_email\
        .library_pid
    assert response['patron_id']
    assert response['patron_name']


def test_patron_information(client, sip2_librarian_martigny_no_email,
                            sip2_patron_martigny_no_email, loc_public_martigny,
                            item_lib_martigny, item2_lib_martigny,
                            circulation_policies, lib_martigny):
    """Test patron information."""
    login_user_via_session(client, sip2_librarian_martigny_no_email.user)
    # checkout
    res, data = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item_lib_martigny.pid,
            patron_pid=sip2_patron_martigny_no_email.pid,
            transaction_user_pid=sip2_librarian_martigny_no_email.pid,
            transaction_location_pid=loc_public_martigny.pid
        )
    )
    assert res.status_code == 200
    actions = data.get('action_applied')
    loan_pid = actions[LoanAction.CHECKOUT].get('pid')
    loan = Loan.get_record_by_pid(loan_pid)
    assert not loan.is_loan_overdue()
    # set loan on overdue
    end_date = datetime.now(timezone.utc) - timedelta(days=7)
    loan['end_date'] = end_date.isoformat()
    loan.update(
        loan,
        dbcommit=True,
        reindex=True
    )
    loan = Loan.get_record_by_pid(loan_pid)
    assert loan.is_loan_overdue()
    loan.create_notification(notification_type='overdue')
    flush_index(NotificationsSearch.Meta.index)
    flush_index(LoansSearch.Meta.index)
    assert number_of_reminders_sent(loan) == 1
    # create request
    res, data = postdata(
        client,
        'api_item.librarian_request',
        dict(
            item_pid=item2_lib_martigny.pid,
            patron_pid=sip2_patron_martigny_no_email.pid,
            pickup_location_pid=loc_public_martigny.pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=sip2_librarian_martigny_no_email.pid
        )
    )
    assert res.status_code == 200
    # get patron information
    response = patron_information(sip2_patron_martigny_no_email.get(
        'patron', {}).get('barcode'))
    assert response

    # checkin
    res, _ = postdata(
        client,
        'api_item.checkin',
        dict(
            item_pid=item_lib_martigny.pid,
            pid=loan_pid,
            transaction_user_pid=sip2_librarian_martigny_no_email.pid,
            transaction_location_pid=loc_public_martigny.pid
        )
    )
    assert res.status_code == 200


def test_item_information(client, sip2_librarian_martigny_no_email,
                          sip2_patron_martigny_no_email, loc_public_martigny,
                          item_lib_martigny,
                          circulation_policies):
    """Test item information."""
    login_user_via_session(client, sip2_librarian_martigny_no_email.user)
    # checkout
    res, data = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item_lib_martigny.pid,
            patron_pid=sip2_patron_martigny_no_email.pid,
            transaction_user_pid=sip2_librarian_martigny_no_email.pid,
            transaction_location_pid=loc_public_martigny.pid
        )
    )
    assert res.status_code == 200
    actions = data.get('action_applied')
    loan_pid = actions[LoanAction.CHECKOUT].get('pid')
    loan = Loan.get_record_by_pid(loan_pid)

    assert not loan.is_loan_overdue()
    # set loan on overdue
    end_date = datetime.now(timezone.utc) - timedelta(days=7)
    loan['end_date'] = end_date.isoformat()
    loan.update(
        loan,
        dbcommit=True,
        reindex=True
    )
    loan = Loan.get_record_by_pid(loan_pid)
    assert loan['state'] == LoanState.ITEM_ON_LOAN
    assert loan.is_loan_overdue()
    loan.create_notification(notification_type='overdue')
    flush_index(NotificationsSearch.Meta.index)
    flush_index(LoansSearch.Meta.index)
    assert number_of_reminders_sent(loan) == 1

    patron_barcode = sip2_patron_martigny_no_email\
        .get('patron', {}).get('barcode')
    item_pid = item_lib_martigny.pid

    # get item information
    response = item_information(
        patron_barcode=patron_barcode,
        item_pid=item_pid
    )
    assert response
    # check required fields in response
    assert all(key in response for key in (
        'item_id',
        'title_id',
        'circulation_status',
        'fee_type',
        'security_marker',
    ))
    assert response['due_date']
    assert response['fee_amount']

    # checkin
    res, _ = postdata(
        client,
        'api_item.checkin',
        dict(
            item_pid=item_lib_martigny.pid,
            pid=loan_pid,
            transaction_user_pid=sip2_librarian_martigny_no_email.pid,
            transaction_location_pid=loc_public_martigny.pid
        )
    )
    assert res.status_code == 200


def test_selfcheck_checkout(client, sip2_librarian_martigny_no_email,
                            sip2_patron_martigny_no_email, loc_public_martigny,
                            item_lib_martigny, librarian2_martigny_no_email,
                            circulation_policies):
    """Test selfcheck checkout."""
    patron_barcode = sip2_patron_martigny_no_email \
        .get('patron', {}).get('barcode')
    item_barcode = item_lib_martigny.get('barcode')

    # selfcheck checkout
    checkout = selfcheck_checkout(
        user_pid=sip2_librarian_martigny_no_email.pid,
        institution_id=sip2_librarian_martigny_no_email.library_pid,
        patron_barcode=patron_barcode,
        item_barcode=item_barcode,
    )
    assert checkout
    assert checkout.is_success
    assert checkout.due_date

    # librarian checkin
    login_user_via_session(client, librarian2_martigny_no_email.user)
    res, _ = postdata(
        client,
        'api_item.checkin',
        dict(
            item_pid=item_lib_martigny.pid,
            transaction_user_pid=librarian2_martigny_no_email.pid,
            transaction_location_pid=loc_public_martigny.pid
        )
    )
    assert res.status_code == 200


def test_selfcheck_checkin(client, sip2_librarian_martigny_no_email,
                           librarian2_martigny_no_email, loc_public_martigny,
                           sip2_patron_martigny_no_email, item_lib_martigny,
                           document, circulation_policies):
    """Test selfcheck checkin."""
    patron_barcode = sip2_patron_martigny_no_email \
        .get('patron', {}).get('barcode')
    item_barcode = item_lib_martigny.get('barcode')

    # librarian checkout
    login_user_via_session(client, librarian2_martigny_no_email.user)
    res, data = postdata(client, 'api_item.checkout', dict(
        item_pid=item_lib_martigny.pid,
        patron_pid=sip2_patron_martigny_no_email.pid,
        transaction_location_pid=loc_public_martigny.pid,
        transaction_user_pid=librarian2_martigny_no_email.pid,
    ))
    assert res.status_code == 200

    # test selfcheck checkin with invalid item barcode
    checkin = selfcheck_checkin(
        user_pid=sip2_librarian_martigny_no_email.pid,
        institution_id=sip2_librarian_martigny_no_email.library_pid,
        patron_barcode=patron_barcode,
        item_barcode='wrong_item_barcode',
    )
    assert checkin
    assert not checkin.is_success

    # selfcheck checkin
    checkin = selfcheck_checkin(
        user_pid=sip2_librarian_martigny_no_email.pid,
        institution_id=sip2_librarian_martigny_no_email.library_pid,
        patron_barcode=patron_barcode,
        item_barcode=item_barcode,
    )
    assert checkin
    assert checkin.is_success
