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

"""Tests Views for patrons."""

import json
from copy import deepcopy

import mock
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import get_json

from rero_ils.modules.items.api import ItemStatus
from rero_ils.modules.loans.api import LoanAction
from rero_ils.modules.patrons.listener import listener_item_at_desk
from rero_ils.modules.patrons.utils import user_has_patron


def test_patron_can_delete(client, librarian_martigny_no_email,
                           patron_martigny_no_email, loc_public_martigny,
                           item_lib_martigny, json_header,
                           circulation_policies):
    """Test patron can delete."""
    login_user_via_session(client, librarian_martigny_no_email.user)
    item = item_lib_martigny
    patron = patron_martigny_no_email
    location = loc_public_martigny

    data = deepcopy(patron_martigny_no_email)
    del data['patron_type']
    assert not data.get_organisation()

    # request
    res = client.post(
        url_for('api_item.librarian_request'),
        data=json.dumps(
            dict(
                item_pid=item.pid,
                pickup_location_pid=location.pid,
                patron_pid=patron.pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200
    data = get_json(res)
    loan_pid = data.get('action_applied')[LoanAction.REQUEST].get('loan_pid')

    links = patron_martigny_no_email.get_links_to_me()
    assert 'loans' in links

    assert not patron_martigny_no_email.can_delete

    reasons = patron_martigny_no_email.reasons_not_to_delete()
    assert 'links' in reasons

    item.cancel_loan(loan_pid=loan_pid)
    assert item.status == ItemStatus.ON_SHELF


def test_patron_utils(client, librarian_martigny_no_email,
                      patron_martigny_no_email, loc_public_martigny,
                      item_lib_martigny, json_header,
                      circulation_policies, librarian_martigny):
    """Test patron utils."""
    login_user_via_session(client, librarian_martigny_no_email.user)
    item = item_lib_martigny
    patron = patron_martigny_no_email
    location = loc_public_martigny

    from rero_ils.modules.patrons.views import get_location_name_from_pid
    assert get_location_name_from_pid(loc_public_martigny.pid) == \
        location.get('name')

    from rero_ils.modules.patrons.views import get_patron_from_pid
    assert get_patron_from_pid(patron.pid) == patron

    from rero_ils.modules.patrons.views import get_checkout_loan_for_item
    assert not get_checkout_loan_for_item(item.pid)

    from rero_ils.modules.patrons.views import get_patron_from_barcode
    assert get_patron_from_barcode(patron.get('barcode')) == patron


def test_librarian_pickup_locations(client, librarian_martigny_no_email,
                                    lib_martigny, loc_public_martigny,
                                    patron_martigny_no_email,
                                    patron_martigny):
    """Test get librarian pickup locations."""
    login_user_via_session(client, librarian_martigny_no_email.user)

    with mock.patch(
        'rero_ils.modules.patrons.api.current_patron',
        librarian_martigny_no_email
    ):
        assert user_has_patron
        pick = librarian_martigny_no_email.get_librarian_pickup_location_pid()
        assert pick == loc_public_martigny.pid

    with mock.patch(
        'rero_ils.modules.patrons.api.current_patron',
        patron_martigny
    ):
        assert user_has_patron
        pick = librarian_martigny_no_email.get_librarian_pickup_location_pid()
        assert not pick
        record = patron_martigny
        del record['roles']
        assert user_has_patron


def test_patron_listener(client, librarian_martigny_no_email,
                         item_lib_fully,
                         lib_fully, loc_public_martigny,
                         patron_martigny_no_email,
                         patron_martigny,
                         loan_pending_martigny, mailbox):
    """Test patron listener."""
    login_user_via_session(client, librarian_martigny_no_email.user)
    requests = item_lib_fully.number_of_requests()
    assert requests == 1
    for request in item_lib_fully.get_requests():
        item_lib_fully.validate_request(**request)
        item_lib_fully.receive(**loan_pending_martigny)

    sender = {}
    data = {'item': item_lib_fully}
    n_msg = len(mailbox)
    listener_item_at_desk(sender, **data)
    assert len(mailbox) == n_msg + 1
