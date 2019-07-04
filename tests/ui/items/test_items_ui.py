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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Tests REST API items."""

# import json
# from utils import get_json, to_relative_url


from flask import url_for
from invenio_accounts.testutils import login_user_via_session


def test_items_ui_permissions(client, item_lib_martigny,
                              loc_public_martigny,
                              patron_martigny_no_email, json_header,
                              circulation_policies):
    """Test record retrieval."""
    item_pid = item_lib_martigny.pid
    pickup_location_pid = loc_public_martigny.pid
    request_url = url_for(
        'item.patron_request',
        viewcode='global',
        item_pid=item_pid,
        pickup_location_pid=pickup_location_pid
    )
    res = client.get(request_url)
    assert res.status_code == 401

    login_user_via_session(client, patron_martigny_no_email.user)
    request_url = url_for(
        'item.patron_request',
        viewcode='global',
        item_pid=item_pid,
        pickup_location_pid=pickup_location_pid
    )
    res = client.get(request_url)
    assert res.status_code == 302
