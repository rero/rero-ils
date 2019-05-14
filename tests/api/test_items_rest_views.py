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

import json
from copy import deepcopy
from datetime import datetime, timedelta

import ciso8601
import mock
import pytest
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import VerifyRecordPermissionPatch, flush_index, get_json

from rero_ils.modules.circ_policies.api import CircPoliciesSearch, CircPolicy
from rero_ils.modules.errors import InvalidRecordID
from rero_ils.modules.items.api import Item, ItemStatus
from rero_ils.modules.loans.api import Loan, LoanAction
from rero_ils.modules.loans.utils import get_extension_params


def test_checkout_no_loan_given(client, librarian_martigny_no_email,
                                patron_martigny_no_email, loc_public_martigny,
                                item_lib_martigny, json_header,
                                circulation_policies):
    """Test checkout item when request loan is not given."""
    login_user_via_session(client, librarian_martigny_no_email.user)
    item = item_lib_martigny
    patron = patron_martigny_no_email
    location = loc_public_martigny
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

    # checkout
    res = client.post(
        url_for('api_item.checkout'),
        data=json.dumps(
            dict(
                item_pid=item.pid,
                patron_pid=patron.pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200
    data = get_json(res)
    loan_pid = data.get('action_applied')[LoanAction.CHECKOUT].get('loan_pid')

    from rero_ils.modules.patrons.views import  \
        get_patron_from_checkout_item_pid
    assert get_patron_from_checkout_item_pid(item.pid) == patron

    res = client.post(
        url_for('api_item.checkin'),
        data=json.dumps(
            dict(
                item_pid=item.pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 403

    res = client.post(
        url_for('api_item.checkin'),
        data=json.dumps(
            dict(
                item_pid=item.pid,
                loan_pid=loan_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200


def test_item_misc(client, librarian_martigny_no_email, lib_martigny,
                   patron_martigny_no_email, loc_public_martigny,
                   item_lib_martigny, json_header, item_type_standard_martigny,
                   circ_policy_short_martigny, patron_type_children_martigny):
    """Test item different functions."""
    login_user_via_session(client, librarian_martigny_no_email.user)
    item = item_lib_martigny
    patron = patron_martigny_no_email
    location = loc_public_martigny
    circ_policy_origin = deepcopy(circ_policy_short_martigny)
    circ_policy = circ_policy_short_martigny

    assert not item.get_extension_count()
    assert not item.get_loan_pid_with_item_in_transit(item.pid)
    assert not item.get_loan_pid_with_item_on_loan(item.pid)
    assert not item.get_item_by_barcode(barcode='does not exist')

    loans = item.get_checked_out_loans('does not exist')

    with pytest.raises(InvalidRecordID):
        assert sum(1 for loan in loans)

    assert 'checkout' in item.actions

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

    res = client.post(
        url_for('api_item.validate_request'),
        data=json.dumps(
            dict(
                item_pid=item.pid,
                loan_pid=loan_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200

    circ_policy['allow_checkout'] = False
    circ_policy['renewal_duration'] = 30

    circ_policy.update(circ_policy, dbcommit=True, reindex=True)
    assert not circ_policy.get('allow_checkout')
    assert 'checkout' not in item.actions

    circ_policy['allow_checkout'] = True
    circ_policy.update(
        circ_policy,
        dbcommit=True,
        reindex=True
    )

    # checkout
    res = client.post(
        url_for('api_item.checkout'),
        data=json.dumps(
            dict(
                item_pid=item.pid,
                patron_pid=patron.pid,
                loan_pid=loan_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200
    assert 'extend_loan' in item.actions

    class current_i18n:
        class locale:
            language = 'fr'
    with mock.patch(
        'rero_ils.modules.items.api.current_i18n',
        current_i18n
    ):
        assert item.get_item_end_date()

    circ_policy.update(circ_policy_origin, dbcommit=True, reindex=True)
    res = client.post(
        url_for('api_item.checkin'),
        data=json.dumps(
            dict(
                item_pid=item.pid,
                loan_pid=loan_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200

    class current_i18n:
        class locale:
            language = 'fr'
    with mock.patch(
        'rero_ils.modules.items.api.current_i18n',
        current_i18n
    ):
        assert not item.get_item_end_date()


def test_automatic_checkin(client, librarian_martigny_no_email, lib_martigny,
                           patron_martigny_no_email, loc_public_martigny,
                           item_lib_martigny, json_header,
                           item_type_standard_martigny,
                           circ_policy_short_martigny,
                           patron_type_children_martigny, lib_saxon,
                           loc_public_saxon, librarian_saxon_no_email):
    """Test item automatic checkin."""
    login_user_via_session(client, librarian_saxon_no_email.user)
    circ_policy_origin = deepcopy(circ_policy_short_martigny)
    circ_policy = circ_policy_short_martigny

    record, actions = item_lib_martigny.automatic_checkin()
    assert actions == {'no': None}

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
    loan_pid = data.get('action_applied')[LoanAction.REQUEST].get('loan_pid')

    res = client.post(
        url_for('api_item.validate_request'),
        data=json.dumps(
            dict(
                item_pid=item_lib_martigny.pid,
                loan_pid=loan_pid,
                transaction_location_pid=loc_public_martigny.pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200

    item = Item.get_record_by_pid(item_lib_martigny.pid)
    assert item.status == ItemStatus.IN_TRANSIT

    record, actions = item.automatic_checkin()
    assert 'receive' in actions

    item.cancel_loan(loan_pid=loan_pid)
    assert item.status == ItemStatus.ON_SHELF


def test_auto_checkin_else(client, librarian_martigny_no_email, lib_martigny,
                           patron_martigny_no_email, loc_public_martigny,
                           item_lib_martigny, json_header,
                           item_type_standard_martigny,
                           circ_policy_short_martigny,
                           patron_type_children_martigny, lib_saxon,
                           loc_public_saxon, librarian_saxon_no_email):
    """Test item automatic checkin other scenarios."""
    login_user_via_session(client, librarian_martigny_no_email.user)
    circ_policy_origin = deepcopy(circ_policy_short_martigny)
    circ_policy = circ_policy_short_martigny

    record, actions = item_lib_martigny.automatic_checkin()
    assert actions == {'no': None}

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
    loan_pid = data.get('action_applied')[LoanAction.REQUEST].get('loan_pid')

    res = client.post(
        url_for('api_item.validate_request'),
        data=json.dumps(
            dict(
                item_pid=item_lib_martigny.pid,
                loan_pid=loan_pid,
                transaction_location_pid=loc_public_martigny.pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200

    item = Item.get_record_by_pid(item_lib_martigny.pid)
    assert item.status == ItemStatus.AT_DESK

    record, actions = item.automatic_checkin()
    assert actions == {'no': None}

    item.cancel_loan(loan_pid=loan_pid)
    assert item.status == ItemStatus.ON_SHELF


def test_item_different_actions(client, librarian_martigny_no_email,
                                lib_martigny,
                                patron_martigny_no_email, loc_public_martigny,
                                item_lib_martigny, json_header,
                                item_type_standard_martigny,
                                circ_policy_short_martigny,
                                patron_type_children_martigny, lib_saxon,
                                loc_public_saxon, librarian_saxon_no_email):
    """Test item possible actions other scenarios."""
    login_user_via_session(client, librarian_martigny_no_email.user)
    circ_policy_origin = deepcopy(circ_policy_short_martigny)
    circ_policy = circ_policy_short_martigny

    patron_pid = patron_martigny_no_email.pid
    res = client.get(
        url_for(
            'api_item.item',
            item_barcode='does not exist',
            patron_pid=patron_pid
        )
    )
    assert res.status_code == 404

    res = client.post(
        url_for('api_item.checkout'),
        data=json.dumps(
            dict(
                item_pid=item_lib_martigny.pid,
                patron_pid=patron_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200
    data = get_json(res)
    loan_pid = data.get('action_applied')[LoanAction.CHECKOUT].get('loan_pid')

    res = client.post(
        url_for('api_item.checkin'),
        data=json.dumps(
            dict(
                item_pid='does not exist',
                loan_pid=loan_pid,
                transaction_location_pid=loc_public_saxon.pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 404

    res = client.post(
        url_for('api_item.checkin'),
        data=json.dumps(
            dict(
                item_pid=item_lib_martigny.pid,
                loan_pid=loan_pid,
                transaction_location_pid=loc_public_saxon.pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200
    data = get_json(res)
    loan_pid = data.get('action_applied')[LoanAction.CHECKIN].get('loan_pid')

    from rero_ils.modules.items.api_views import prior_checkout_actions
    data = {'loan_pid': loan_pid}
    return_data = prior_checkout_actions(item_lib_martigny, data)
    assert return_data == {}
