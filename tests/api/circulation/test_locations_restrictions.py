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

"""Tests REST API to update loan pickup locations."""


from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import get_json

from rero_ils.modules.items.utils import item_pid_to_object
from rero_ils.modules.loans.api import Loan
from rero_ils.modules.loans.utils import can_be_requested
from rero_ils.modules.utils import get_ref_for_pid


def test_item_pickup_location(
        client, librarian_martigny, item2_lib_martigny):
    """Test get item pickup locations."""
    login_user_via_session(client, librarian_martigny.user)
    # test with dummy data will return 404
    res = client.get(
        url_for(
            'api_item.get_pickup_locations',
            item_pid='dummy_pid'
        )
    )
    assert res.status_code == 404
    # test with an existing item
    res = client.get(
        url_for(
            'api_item.get_pickup_locations',
            item_pid=item2_lib_martigny.pid
        )
    )
    assert res.status_code == 200
    data = get_json(res)
    assert 'locations' in data


def test_location_disallow_request(
    item_lib_martigny, item_lib_martigny_data, loc_public_martigny,
    loc_public_martigny_data, loc_public_saxon, lib_martigny, patron_martigny,
    circulation_policies
):
    """Test a request when location disallow request."""
    item = item_lib_martigny
    location = loc_public_martigny

    # update location to disallow request
    location['allow_request'] = False
    location.update(location, dbcommit=True, reindex=True)

    # Create "virtual" Loan (not registered)
    loan = Loan({
        'item_pid': item_pid_to_object(item_lib_martigny.pid),
        'library_pid': lib_martigny.pid,
        'patron_pid': patron_martigny.pid
    })
    assert not can_be_requested(loan)

    # update item to set a temporary location allowing request
    #   owning location disallow request, but temporary location allow request
    #   then the request could be accepted (for locations checks)

    item['temporary_location'] = {
        '$ref': get_ref_for_pid('loc', loc_public_saxon.pid)
    }
    item.update(item, dbcommit=True, reindex=True)
    assert loc_public_saxon['allow_request']
    assert can_be_requested(loan)

    # reset fixtures
    item.update(item_lib_martigny_data, dbcommit=True, reindex=True)
    location.update(loc_public_martigny_data, dbcommit=True, reindex=True)


def test_holding_pickup_location(
        client, patron_martigny, holding_lib_martigny):
    """Test get holding pickup locations for patron."""
    login_user_via_session(client, patron_martigny.user)
    # test with dummy data will return 404
    res = client.get(
        url_for(
            'api_holding.get_pickup_locations',
            holding_pid='dummy_pid'
        )
    )
    assert res.status_code == 404
    # test with an existing holding
    res = client.get(
        url_for(
            'api_holding.get_pickup_locations',
            holding_pid=holding_lib_martigny.pid
        )
    )
    assert res.status_code == 200
    data = get_json(res)
    assert 'locations' in data
