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
from invenio_accounts.testutils import login_user_via_session
from invenio_jsonschemas import current_jsonschemas
from utils import get_json, item_record_to_a_specific_loan_state, login_user

from rero_ils.modules.loans.models import LoanState
from rero_ils.modules.utils import get_schema_for_resource


def test_loan_can_extend(client, patron_martigny, item_lib_martigny,
                         loc_public_martigny, librarian_martigny,
                         circulation_policies, json_header):
    """Test is loan can extend."""
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
    login_user(client, patron_martigny)
    response = client.get(list_url, headers=json_header)
    assert response.status_code == 200
    assert get_json(response) == {
        'can': False,
        'reasons': ['Circulation policies disallows the operation.']
    }


def test_loan_circulation_policy(
    client, patron_martigny, librarian_martigny,
    item_on_loan_martigny_patron_and_loan_on_loan
):
    """Test dumping of circulation policy related to a loan."""
    _, _, loan = item_on_loan_martigny_patron_and_loan_on_loan
    base_url_for = 'api_loan.dump_loan_current_circulation_policy'
    api_url = url_for(base_url_for, loan_pid=loan.pid)
    dummy_url = url_for(base_url_for, loan_pid='dummy_pid')

    # Patron user cannot access to this API
    login_user_via_session(client, patron_martigny.user)
    response = client.get(api_url)
    assert response.status_code == 403

    # Librarian user can access to this API
    login_user_via_session(client, librarian_martigny.user)
    response = client.get(api_url)
    assert response.status_code == 200
    data = get_json(response)
    cipo_schema = get_schema_for_resource('cipo')
    data['$schema'] = current_jsonschemas.path_to_url(cipo_schema)

    response = client.get(dummy_url)
    assert response.status_code == 404
