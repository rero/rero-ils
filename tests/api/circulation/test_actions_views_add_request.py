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

"""Tests REST API methods in the item api_views."""


from invenio_accounts.testutils import login_user_via_session
from utils import postdata

from rero_ils.modules.loans.api import Loan, LoanAction, LoanState, \
    get_last_transaction_loc_for_item, get_loans_by_patron_pid


def test_items_failed_actions(
        client, librarian_martigny_no_email,
        patron_martigny_no_email, loc_public_martigny, loc_public_saxon,
        item_lib_martigny, item2_lib_martigny, circulation_policies):
    """Test item failed actions."""
    login_user_via_session(client, librarian_martigny_no_email.user)

    # test fails for a request with no pickup_location_pid
    res, _ = postdata(
        client,
        'api_item.librarian_request',
        dict(
            item_pid=item_lib_martigny.pid,
            patron_pid=patron_martigny_no_email.pid
        )
    )
    assert res.status_code == 403

    # test fails for a request with no item given
    res, _ = postdata(
        client,
        'api_item.librarian_request',
        dict(
            patron_pid=patron_martigny_no_email.pid
        )
    )
    assert res.status_code == 400
