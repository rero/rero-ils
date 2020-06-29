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

import mock
from invenio_accounts.testutils import login_user_via_session
from utils import postdata

from rero_ils.modules.items.models import ItemStatus
from rero_ils.modules.loans.api import LoanAction
from rero_ils.modules.patrons.utils import user_has_patron


def test_patron_can_delete(client, librarian_martigny_no_email,
                           patron_martigny_no_email, loc_public_martigny,
                           item_lib_martigny, json_header, lib_martigny,
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
    res, data = postdata(
        client,
        'api_item.librarian_request',
        dict(
            item_pid=item.pid,
            pickup_location_pid=location.pid,
            patron_pid=patron.pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny_no_email.pid
        )
    )
    assert res.status_code == 200
    loan_pid = data.get('action_applied')[LoanAction.REQUEST].get('pid')

    links = patron_martigny_no_email.get_links_to_me()
    assert 'loans' in links

    assert not patron_martigny_no_email.can_delete

    reasons = patron_martigny_no_email.reasons_not_to_delete()
    assert 'links' in reasons

    res, data = postdata(
        client,
        'api_item.cancel_item_request',
        dict(
            pid=loan_pid,
            transaction_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny_no_email.pid
        )
    )
    assert res.status_code == 200
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
