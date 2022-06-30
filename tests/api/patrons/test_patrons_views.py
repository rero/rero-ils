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

"""Tests Views for patrons."""

from copy import deepcopy

from invenio_accounts.testutils import login_user_via_session
from utils import postdata

from rero_ils.modules.cli.utils import create_personal
from rero_ils.modules.items.models import ItemStatus
from rero_ils.modules.loans.models import LoanAction


def test_patron_can_delete(client, librarian_martigny,
                           patron_martigny, loc_public_martigny,
                           item_lib_martigny, json_header, lib_martigny,
                           circulation_policies):
    """Test patron can delete."""
    login_user_via_session(client, librarian_martigny.user)
    item = item_lib_martigny
    patron = patron_martigny
    location = loc_public_martigny

    data = deepcopy(patron_martigny)
    del data['patron']['type']
    assert not data.organisation

    # request
    res, data = postdata(
        client,
        'api_item.librarian_request',
        dict(
            item_pid=item.pid,
            pickup_location_pid=location.pid,
            patron_pid=patron.pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny.pid
        )
    )
    assert res.status_code == 200
    loan_pid = data.get('action_applied')[LoanAction.REQUEST].get('pid')

    can, reasons = patron_martigny.can_delete
    assert not can
    assert reasons['links']['loans']

    res, data = postdata(
        client,
        'api_item.cancel_item_request',
        dict(
            pid=loan_pid,
            transaction_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny.pid
        )
    )
    assert res.status_code == 200
    assert item.status == ItemStatus.ON_SHELF


def test_patron_utils(client, librarian_martigny,
                      patron_martigny, loc_public_martigny,
                      item_lib_martigny, json_header,
                      circulation_policies):
    """Test patron utils."""
    login_user_via_session(client, librarian_martigny.user)
    item = item_lib_martigny
    patron = patron_martigny
    location = loc_public_martigny

    from rero_ils.modules.patrons.views import get_location_name_from_pid
    assert get_location_name_from_pid(loc_public_martigny.pid) == \
        location.get('name')

    from rero_ils.modules.patrons.views import get_patron_from_pid
    assert get_patron_from_pid(patron.pid) == patron

    from rero_ils.modules.patrons.views import get_checkout_loan_for_item
    assert not get_checkout_loan_for_item(item.pid)


def test_patron_authenticate(client, patron_martigny, patron_martigny_data,
                             system_librarian_martigny, default_user_password):
    """Test for patron authenticate."""
    # parameters
    token = 'Or7DTg1WT34cLKuSMcS7WzhdhxtKklpTizb1Hn2H0aaV5Vig6nden63VEqBE'
    token_url_data = {'access_token': token}
    username = patron_martigny_data['username']
    password = default_user_password

    create_personal(
        name='token_test',
        user_id=system_librarian_martigny['user_id'],
        access_token=token
    )

    # Missing access_token parameter
    res, _ = postdata(
        client, 'api_patrons.patron_authenticate')
    assert res.status_code == 401

    # Missing parameters (username and password)
    res, _ = postdata(
        client, 'api_patrons.patron_authenticate', url_data=token_url_data)
    assert res.status_code == 400

    # User not found
    post_data = {'username': 'foo', 'password': 'bar'}
    res, _ = postdata(
        client,
        'api_patrons.patron_authenticate',
        post_data,
        url_data=token_url_data
    )
    assert res.status_code == 404

    # User found, bad password
    post_data = {'username': username, 'password': 'bar'}
    res, _ = postdata(
        client,
        'api_patrons.patron_authenticate',
        post_data,
        url_data=token_url_data
    )
    assert res.status_code == 401

    # User found
    post_data = {'username': username, 'password': password}
    res, output = postdata(
        client,
        'api_patrons.patron_authenticate',
        post_data,
        url_data=token_url_data
    )
    assert res.status_code == 200
    assert output['city'] == patron_martigny_data['city']
    assert output['fullname'] == patron_martigny_data['first_name'] + ' ' +\
        patron_martigny_data['last_name']
    assert 'blocked' not in output
