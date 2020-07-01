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


def test_checkout_missing_parameters(
        client,
        librarian_martigny_no_email,
        lib_martigny,
        loc_public_martigny,
        patron_martigny_no_email,
        item_lib_martigny,
        circulation_policies):
    """Test checkout with missing parameters.

    Are needed:
        - item_pid_value
        - patron_pid
        - transaction_location_pid or transaction_library_pid
        - transaction_user_pid
    """
    login_user_via_session(client, librarian_martigny_no_email.user)
    item = item_lib_martigny
    assert item.status == ItemStatus.ON_SHELF

    # test fails when missing required parameter
    res, _ = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item.pid
        )
    )
    assert res.status_code == 400
    res, _ = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item.pid,
            patron_pid=patron_martigny_no_email.pid
        )
    )
    assert res.status_code == 400
    res, _ = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item.pid,
            patron_pid=patron_martigny_no_email.pid,
            transaction_user_pid=librarian_martigny_no_email.pid
        )
    )
    assert res.status_code == 400


def test_checkout(
        client,
        librarian_martigny_no_email,
        lib_martigny,
        loc_public_martigny,
        patron_martigny_no_email,
        item_lib_martigny,
        circulation_policies,
        item_on_shelf_martigny_patron_and_loan_pending):
    """Test a successful frontend checkout action."""
    login_user_via_session(client, librarian_martigny_no_email.user)
    item = item_lib_martigny
    assert item.status == ItemStatus.ON_SHELF

    params = dict(
        item_pid=item.pid,
        patron_pid=patron_martigny_no_email.pid,
        transaction_user_pid=librarian_martigny_no_email.pid,
        transaction_location_pid=loc_public_martigny.pid
    )

    # test is done WITHOUT loan PID
    res, _ = postdata(
        client,
        'api_item.checkout',
        params
    )
    assert res.status_code == 200

    # test WITH loan PID
    item, patron_pid, loan = item_on_shelf_martigny_patron_and_loan_pending
    assert item.status == ItemStatus.ON_SHELF
    params['item_pid'] = item.pid
    params['pid'] = loan.pid
    res, _ = postdata(
        client,
        'api_item.checkout',
        params
    )
    assert res.status_code == 200
