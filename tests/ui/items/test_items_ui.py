#
# This file is part of RERO ILS.
# Copyright (C) 2017 RERO.
#
# RERO ILS is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# RERO ILS is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RERO ILS; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

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
