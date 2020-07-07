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


def test_item_pickup_location(
        client, librarian_martigny_no_email, item2_lib_martigny):
    """Test get item pickup locations."""
    login_user_via_session(client, librarian_martigny_no_email.user)
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
