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

import json

import mock
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import get_json

from rero_ils.modules.items.api import Item
from rero_ils.modules.items.views import not_available_reasons
from rero_ils.modules.loans.api import LoanAction


def test_item_availability(
        client, item_lib_martigny, loc_public_saxon,
        librarian_martigny_no_email, patron_martigny_no_email,
        circulation_policies, librarian_saxon_no_email):
    """Test item availability."""
    def available_status(pid, user):
        """Returns item availability."""
        login_user_via_session(client, user)
        res = client.get(
            url_for(
                'api_item.item_availability',
                item_pid=pid,
            )
        )
        assert res.status_code == 200
        data = get_json(res)
        return data.get('availability')

    assert available_status(
        item_lib_martigny.pid, librarian_martigny_no_email.user)
    assert item_lib_martigny.available
    assert not not_available_reasons(item_lib_martigny)
    login_user_via_session(client, librarian_martigny_no_email.user)

    res = client.post(
        url_for('api_item.librarian_request'),
        data=json.dumps(
            dict(
                item_pid=item_lib_martigny.pid,
                pickup_location_pid=loc_public_saxon.pid,
                patron_pid=patron_martigny_no_email.pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200
    data = get_json(res)
    actions = data.get('action_applied')
    loan_pid = actions[LoanAction.REQUEST].get('pid')
    assert not item_lib_martigny.available
    assert not available_status(
        item_lib_martigny.pid, librarian_martigny_no_email.user)
    assert not_available_reasons(item_lib_martigny) == '(1 requests)'

    # validate request
    res = client.post(
        url_for('api_item.validate_request'),
        data=json.dumps(
            dict(
                item_pid=item_lib_martigny.pid,
                pid=loan_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200
    assert not item_lib_martigny.available
    assert not available_status(
        item_lib_martigny.pid, librarian_martigny_no_email.user)
    assert not item_lib_martigny.available
    item = Item.get_record_by_pid(item_lib_martigny.pid)
    assert not_available_reasons(item) == 'in transit (1 requests)'

    login_user_via_session(client, librarian_saxon_no_email.user)
    # receive
    res = client.post(
        url_for('api_item.receive'),
        data=json.dumps(
            dict(
                item_pid=item_lib_martigny.pid,
                pid=loan_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200
    assert not item_lib_martigny.available
    assert not available_status(
        item_lib_martigny.pid, librarian_saxon_no_email.user)
    item = Item.get_record_by_pid(item_lib_martigny.pid)
    assert not item.available
    assert not_available_reasons(item) == '(1 requests)'

    # checkout
    res = client.post(
        url_for('api_item.checkout'),
        data=json.dumps(
            dict(
                item_pid=item_lib_martigny.pid,
                patron_pid=patron_martigny_no_email.pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200

    item = Item.get_record_by_pid(item_lib_martigny.pid)
    assert not item.available
    assert not available_status(
        item.pid, librarian_martigny_no_email.user)

    class current_i18n:
        class locale:
            language = 'fr'
    with mock.patch(
        'rero_ils.modules.items.api.current_i18n',
        current_i18n
    ):
        end_date = item.get_item_end_date()
        assert not_available_reasons(item) == 'due until ' + end_date
