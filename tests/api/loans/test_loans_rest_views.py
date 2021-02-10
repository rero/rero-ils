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

"""Tests REST API loans."""

from flask import url_for
from utils import get_json, item_record_to_a_specific_loan_state, login_user

from rero_ils.modules.loans.api import LoanState


def test_loan_can_extend(client, patron_martigny, item_lib_martigny,
                         loc_public_martigny, librarian_martigny,
                         circulation_policies, json_header):
    """Test is loan can extend."""
    login_user(client, patron_martigny)
    params = {
        'patron_pid': patron_martigny.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid,
        'pickup_location_pid': loc_public_martigny.pid,
    }
    item, loan = item_record_to_a_specific_loan_state(
        item=item_lib_martigny, loan_state=LoanState.ITEM_ON_LOAN,
        params=params, copy_item=True)

    list_url = url_for(
        'api_loan.can_extend', loan_pid=loan.pid)
    response = client.get(list_url, headers=json_header)
    assert response.status_code == 200
    assert get_json(response) == {
        'can': False,
        'reasons': ['Circulation policies disallows the operation.']
    }
