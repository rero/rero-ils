# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2020 RERO
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

"""Tests REST checkout API methods in the item api_views."""


from invenio_accounts.testutils import login_user_via_session
from utils import postdata

from rero_ils.modules.items.models import ItemStatus


def test_extend_loan_missing_parameters(
        client,
        librarian_martigny,
        lib_martigny,
        loc_public_martigny,
        circulation_policies,
        item_on_loan_martigny_patron_and_loan_on_loan):
    """Test extend loan with missing parameters.

    Are needed:
        - transaction_location_pid or transaction_library_pid
        - transaction_user_pid
    """
    login_user_via_session(client, librarian_martigny.user)
    item, patron, loan = item_on_loan_martigny_patron_and_loan_on_loan
    assert item.status == ItemStatus.ON_LOAN

    # test fails when missing required parameter
    res, _ = postdata(
        client,
        'api_item.extend_loan',
        dict(
            item_pid=item.pid
        )
    )
    assert res.status_code == 400
    res, _ = postdata(
        client,
        'api_item.extend_loan',
        dict(
            item_pid=item.pid,
            transaction_location_pid=loc_public_martigny.pid
        )
    )
    assert res.status_code == 400
    res, _ = postdata(
        client,
        'api_item.extend_loan',
        dict(
            item_pid=item.pid,
            transaction_user_pid=librarian_martigny.pid
        )
    )
    assert res.status_code == 400


def test_extend_loan(
        client,
        librarian_martigny,
        lib_martigny,
        loc_public_martigny,
        circulation_policies,
        item_on_loan_martigny_patron_and_loan_on_loan,
        yesterday):
    """Test frontend extend action."""
    item, patron, loan = item_on_loan_martigny_patron_and_loan_on_loan
    # Update loan `end_date` to play with "extend" function without problem
    loan['end_date'] = loan['start_date']
    loan.update(loan, dbcommit=True, reindex=True)

    assert item.status == ItemStatus.ON_LOAN

    # Test extend for a blocked patron
    patron['patron']['blocked'] = True
    patron['patron']['blocked_note'] = 'Dummy reason'
    patron.update(patron, dbcommit=True, reindex=True)

    params = dict(
        item_pid=item.pid,
        transaction_user_pid=librarian_martigny.pid,
        transaction_location_pid=loc_public_martigny.pid
    )

    login_user_via_session(client, librarian_martigny.user)
    res, _ = postdata(client, 'api_item.extend_loan', params)
    assert res.status_code == 403

    # Test for an expired patron
    del patron['patron']['blocked']
    del patron['patron']['blocked_note']
    original_exp_date = patron['patron']['expiration_date']
    patron['patron']['expiration_date'] = yesterday.strftime('%Y-%m-%d')
    patron.update(patron, dbcommit=True, reindex=True)

    res, _ = postdata(client, 'api_item.extend_loan', params)
    assert res.status_code == 403

    patron['patron']['expiration_date'] = original_exp_date
    patron.update(patron, dbcommit=True, reindex=True)

    # With only needed parameters
    res, _ = postdata(client, 'api_item.extend_loan', params)
    assert res.status_code == 200
