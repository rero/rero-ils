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

"""Tests REST librarian request API methods in the item api_views."""


from invenio_accounts.testutils import login_user_via_session
from utils import postdata

from rero_ils.modules.loans.api import Loan, LoanAction, LoanState, \
    get_last_transaction_loc_for_item, get_loans_by_patron_pid


def test_add_request_failed_actions(
        client, librarian_martigny_no_email, lib_martigny,
        patron_martigny_no_email, loc_public_martigny, item_lib_martigny,
        circulation_policies):
    """Test item failed actions."""
    login_user_via_session(client, librarian_martigny_no_email.user)

    # test fails for a request with a missing parameter pickup_location_pid
    res, data = postdata(
        client,
        'api_item.librarian_request',
        dict(
            item_pid=item_lib_martigny.pid,
            patron_pid=patron_martigny_no_email.pid
        )
    )
    assert res.status_code == 400

    # test fails for a request with a missing parameter item_pid
    # when item record not found in database, api returns 404
    res, data = postdata(
        client,
        'api_item.librarian_request',
        dict(
            patron_pid=patron_martigny_no_email.pid,
            pickup_location_pid=loc_public_martigny.pid
        )
    )
    assert res.status_code == 404

    # test fails for a request with a missing parameter patron_pid
    res, data = postdata(
        client,
        'api_item.librarian_request',
        dict(
            item_pid=item_lib_martigny.pid,
            pickup_location_pid=loc_public_martigny.pid
        )
    )
    assert res.status_code == 400

    # test fails for a request with a missing parameter transaction_library_pid
    res, data = postdata(
        client,
        'api_item.librarian_request',
        dict(
            item_pid=item_lib_martigny.pid,
            patron_pid=patron_martigny_no_email.pid,
            pickup_location_pid=loc_public_martigny.pid
        )
    )
    assert res.status_code == 400


def test_add_request(
        client, librarian_martigny_no_email, lib_martigny,
        patron_martigny_no_email, loc_public_martigny, item_lib_martigny,
        circulation_policies, patron2_martigny_no_email):
    """Test a successful frontend add request action."""
    # test passes when all required parameters are given
    # test passes when the transaction libarary pid is given
    login_user_via_session(client, librarian_martigny_no_email.user)
    res, data = postdata(
        client,
        'api_item.librarian_request',
        dict(
            item_pid=item_lib_martigny.pid,
            patron_pid=patron_martigny_no_email.pid,
            pickup_location_pid=loc_public_martigny.pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny_no_email.pid
        )
    )
    assert res.status_code == 200

    # test passes when the transaction location pid is given
    login_user_via_session(client, librarian_martigny_no_email.user)
    res, data = postdata(
        client,
        'api_item.librarian_request',
        dict(
            item_pid=item_lib_martigny.pid,
            patron_pid=patron2_martigny_no_email.pid,
            pickup_location_pid=loc_public_martigny.pid,
            transaction_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny_no_email.pid
        )
    )
    assert res.status_code == 200
