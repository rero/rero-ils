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

import json
from datetime import datetime, timedelta

import ciso8601
import mock
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import VerifyRecordPermissionPatch, flush_index, get_json

from rero_ils.modules.circ_policies.api import CircPoliciesSearch
from rero_ils.modules.items.api import Item, ItemStatus
from rero_ils.modules.loans.api import Loan, LoanAction
from rero_ils.modules.loans.utils import get_extension_params


def test_items_permissions(client, item_on_loan, user_patron_no_email,
                           json_header):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.item_item', pid_value='item1')
    post_url = url_for('invenio_records_rest.item_list')

    res = client.get(item_url)
    assert res.status_code == 401

    res = client.post(
        post_url,
        data={},
        headers=json_header
    )
    assert res.status_code == 401

    res = client.put(
        url_for('invenio_records_rest.item_item', pid_value='item1'),
        data={},
        headers=json_header
    )

    res = client.delete(item_url)
    assert res.status_code == 401

    views = [
        'api_item.checkout',
        'api_item.checkin',
        'api_item.automatic_checkin',
        'api_item.cancel_loan',
        'api_item.lose',
        'api_item.validate_request',
        'api_item.receive',
        'api_item.return_missing',
        'api_item.extend_loan',
        'api_item.librarian_request'
    ]
    for view in views:
        res = client.post(
            url_for(view),
            data={}
        )
        assert res.status_code == 401
    res = client.get(
        url_for('api_item.requested_loans', library_pid='test'),
        data={}
    )
    assert res.status_code == 401
    login_user_via_session(client, user_patron_no_email.user)
    for view in views:
        res = client.post(
            url_for(view),
            data={}
        )
        assert res.status_code == 403
    res = client.get(
        url_for('api_item.requested_loans', library_pid='test'),
        data={}
    )
    assert res.status_code == 403


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_items_post_put_delete(client, document, location, item_type,
                               item_on_loan_data, json_header):
    """Test record retrieval."""
    # Create record / POST
    item_url = url_for('invenio_records_rest.item_item', pid_value='1')
    post_url = url_for('invenio_records_rest.item_list')
    list_url = url_for('invenio_records_rest.item_list', q='pid:1')

    item_on_loan_data['pid'] = '1'
    res = client.post(
        post_url,
        data=json.dumps(item_on_loan_data),
        headers=json_header
    )
    assert res.status_code == 201

    # Check that the returned record matches the given data
    data = get_json(res)
    assert data['metadata'] == item_on_loan_data

    res = client.get(item_url)
    assert res.status_code == 200
    data = get_json(res)
    assert item_on_loan_data == data['metadata']

    # Update record/PUT
    data = item_on_loan_data
    data['call_number'] = 'Test Name'
    res = client.put(
        item_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 200
    # assert res.headers['ETag'] != '"{}"'.format(librarie.revision_id)

    # Check that the returned record matches the given data
    data = get_json(res)
    assert data['metadata']['call_number'] == 'Test Name'

    res = client.get(item_url)
    assert res.status_code == 200

    data = get_json(res)
    assert data['metadata']['call_number'] == 'Test Name'

    res = client.get(list_url)
    assert res.status_code == 200

    data = get_json(res)['hits']['hits'][0]
    assert data['metadata']['call_number'] == 'Test Name'

    # Delete record/DELETE
    res = client.delete(item_url)
    assert res.status_code == 204

    res = client.get(item_url)
    assert res.status_code == 410


def test_items_failed_actions(client, user_librarian_no_email,
                              user_patron_no_email, location, item_type,
                              item_on_shelf, json_header):
    """."""
    login_user_via_session(client, user_librarian_no_email.user)
    item = item_on_shelf
    item_pid = item.pid
    patron_pid = user_patron_no_email.pid

    # no item_pid
    res = client.post(
        url_for('api_item.checkout'),
        data=json.dumps(
            dict(
                patron_pid=patron_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 500

    # failed checkout no patron_pid
    res = client.post(
        url_for('api_item.checkout'),
        data=json.dumps(
            dict(
                item_pid=item_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 403

    # no pickup
    res = client.post(
        url_for('api_item.librarian_request'),
        data=json.dumps(
            dict(
                item_pid=item_pid,
                patron_pid=patron_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 403


def test_items_simple_checkout(client, user_librarian_no_email,
                               user_patron_no_email, location, item_type,
                               item_on_shelf, json_header,
                               circulation_policies):
    """."""
    login_user_via_session(client, user_librarian_no_email.user)
    item = item_on_shelf
    item_pid = item.pid
    patron_pid = user_patron_no_email.pid
    assert not item.is_loaned_to_patron(user_patron_no_email.get('barcode'))
    assert item.can_delete
    assert item.available

    # checkout
    res = client.post(
        url_for('api_item.checkout'),
        data=json.dumps(
            dict(
                item_pid=item_pid,
                patron_pid=patron_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200
    data = get_json(res)
    item_data = data.get('metadata')
    actions = data.get('action_applied')
    assert item_data.get('status') == ItemStatus.ON_LOAN
    assert actions.get(LoanAction.CHECKOUT)
    loan_pid = actions[LoanAction.CHECKOUT].get('loan_pid')
    item = Item.get_record_by_pid(item_pid)
    assert item.is_loaned_to_patron(user_patron_no_email.get('barcode'))
    assert not item.available
    assert not item.can_delete

    # get loans for the patron
    res = client.get(
        url_for('api_item.loans', patron_pid=patron_pid)
    )
    assert res.status_code == 200
    data = get_json(res)
    assert data.get('hits').get('total') == 1

    # checkin
    res = client.post(
        url_for('api_item.checkin'),
        data=json.dumps(
            dict(
                item_pid=item_pid,
                loan_pid=loan_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200
    data = get_json(res)
    item_data = data.get('metadata')
    actions = data.get('action_applied')
    assert item_data.get('status') == ItemStatus.ON_SHELF
    assert actions.get(LoanAction.CHECKIN)


def test_checkout_default_policy(client, library,
                                 user_librarian_no_email_specific,
                                 user_patron_no_email_specific,
                                 location, item_type_specific,
                                 item_specific, json_header,
                                 circ_policy_short, circ_policy):
    """Test circ policy parameters"""
    login_user_via_session(client, user_librarian_no_email_specific.user)
    item = item_specific
    item_pid = item.pid
    patron_pid = user_patron_no_email_specific.pid

    # checkout
    res = client.post(
        url_for('api_item.checkout'),
        data=json.dumps(
            dict(
                item_pid=item_pid,
                patron_pid=patron_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200

    data = get_json(res)

    actions = data.get('action_applied')
    loan = actions[LoanAction.CHECKOUT]
    end_date = loan.get('end_date')
    start_date = loan.get('start_date')
    checkout_duration = (ciso8601.parse_datetime(
        end_date) - ciso8601.parse_datetime(start_date)).days

    assert checkout_duration >= circ_policy.get('checkout_duration')

    # checkin
    res = client.post(
        url_for('api_item.checkin'),
        data=json.dumps(
            dict(
                item_pid=item_pid,
                loan_pid=loan.get('loan_pid')
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200


def test_checkout_library_level_policy(client, library,
                                       user_librarian_no_email_specific,
                                       user_patron_no_email_specific,
                                       location, item_type_specific,
                                       item_specific, json_header,
                                       circ_policy_short_library):
    """Test circ policy parameters"""
    login_user_via_session(client, user_librarian_no_email_specific.user)
    item = item_specific
    item_pid = item.pid
    patron_pid = user_patron_no_email_specific.pid

    # checkout
    res = client.post(
        url_for('api_item.checkout'),
        data=json.dumps(
            dict(
                item_pid=item_pid,
                patron_pid=patron_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200

    data = get_json(res)

    actions = data.get('action_applied')
    loan = actions[LoanAction.CHECKOUT]
    end_date = loan.get('end_date')
    start_date = loan.get('start_date')
    checkout_duration = (ciso8601.parse_datetime(
        end_date) - ciso8601.parse_datetime(start_date)).days
    assert checkout_duration >= circ_policy_short_library.get(
        'checkout_duration')

    # checkin
    res = client.post(
        url_for('api_item.checkin'),
        data=json.dumps(
            dict(
                item_pid=item_pid,
                loan_pid=loan.get('loan_pid')
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200


def test_checkout_organisation_policy(client, library,
                                      user_librarian_no_email,
                                      user_patron_no_email,
                                      location, item_type,
                                      item_on_shelf, json_header,
                                      circ_policy_short, circ_policy):
    """Test circ policy parameters"""
    login_user_via_session(client, user_librarian_no_email.user)
    item = item_on_shelf
    item_pid = item.pid
    patron_pid = user_patron_no_email.pid

    # checkout
    res = client.post(
        url_for('api_item.checkout'),
        data=json.dumps(
            dict(
                item_pid=item_pid,
                patron_pid=patron_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200

    data = get_json(res)

    actions = data.get('action_applied')
    loan = actions[LoanAction.CHECKOUT]
    end_date = loan.get('end_date')
    start_date = loan.get('start_date')
    checkout_duration = (ciso8601.parse_datetime(
        end_date) - ciso8601.parse_datetime(start_date)).days
    assert checkout_duration >= circ_policy_short.get(
        'checkout_duration')

    # checkin
    res = client.post(
        url_for('api_item.checkin'),
        data=json.dumps(
            dict(
                item_pid=item_pid,
                loan_pid=loan.get('loan_pid')
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200


def test_items_requests(client, user_librarian_no_email,
                        user_patron_no_email, location, item_type,
                        item_on_shelf, json_header):
    """."""
    login_user_via_session(client, user_librarian_no_email.user)
    item = item_on_shelf
    item_pid = item.pid
    patron = user_patron_no_email
    patron_pid = patron.pid
    library_pid = user_librarian_no_email\
        .replace_refs()['library']['pid']

    assert not item.patron_request_rank(patron.get('barcode'))
    assert not item.is_requested_by_patron(patron.get('barcode'))
    # request
    res = client.post(
        url_for('api_item.librarian_request'),
        data=json.dumps(
            dict(
                item_pid=item_pid,
                pickup_location_pid=location.pid,
                patron_pid=patron_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200
    data = get_json(res)
    item_data = data.get('metadata')
    actions = data.get('action_applied')
    assert item_data.get('status') == ItemStatus.ON_SHELF
    assert actions.get(LoanAction.REQUEST)
    loan_pid = actions[LoanAction.REQUEST].get('loan_pid')
    item = Item.get_record_by_pid(item_pid)
    assert item.patron_request_rank(patron.get('barcode')) == 1
    assert item.is_requested_by_patron(patron.get('barcode'))

    # checkout
    res = client.post(
        url_for('api_item.checkout'),
        data=json.dumps(
            dict(
                item_pid=item_pid,
                loan_pid=loan_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200
    data = get_json(res)
    item_data = data.get('metadata')
    actions = data.get('action_applied')
    assert item_data.get('status') == ItemStatus.ON_LOAN
    assert actions.get(LoanAction.CHECKOUT)

    res = client.post(
        url_for('api_item.checkin'),
        data=json.dumps(
            dict(
                item_pid=item_pid,
                loan_pid=loan_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200
    data = get_json(res)
    item_data = data.get('metadata')
    actions = data.get('action_applied')
    assert item_data.get('status') == ItemStatus.ON_SHELF
    assert actions.get(LoanAction.CHECKIN)

    # request
    res = client.post(
        url_for('api_item.librarian_request'),
        data=json.dumps(
            dict(
                item_pid=item_pid,
                pickup_location_pid=location.pid,
                patron_pid=patron_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200
    data = get_json(res)
    item_data = data.get('metadata')
    actions = data.get('action_applied')
    assert item_data.get('status') == ItemStatus.ON_SHELF
    assert actions.get(LoanAction.REQUEST)
    loan_pid = actions[LoanAction.REQUEST].get('loan_pid')

    # get requests to validate
    res = client.get(
        url_for('api_item.requested_loans', library_pid='not exists')
    )
    assert res.status_code == 500

    res = client.get(
        url_for('api_item.requested_loans', library_pid=library_pid)
    )
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total'] == 1
    assert len(data['hits']['hits']) == 1

    # validate request
    res = client.post(
        url_for('api_item.validate_request'),
        data=json.dumps(
            dict(
                item_pid=item_pid,
                loan_pid=loan_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200
    data = get_json(res)
    item_data = data.get('metadata')
    actions = data.get('action_applied')
    assert item_data.get('status') == ItemStatus.AT_DESK
    assert actions.get(LoanAction.VALIDATE)

    # checkout
    res = client.post(
        url_for('api_item.checkout'),
        data=json.dumps(
            dict(
                item_pid=item_pid,
                loan_pid=loan_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200
    data = get_json(res)
    item_data = data.get('metadata')
    actions = data.get('action_applied')
    assert item_data.get('status') == ItemStatus.ON_LOAN
    assert actions.get(LoanAction.CHECKOUT)

    res = client.post(
        url_for('api_item.checkin'),
        data=json.dumps(
            dict(
                item_pid=item_pid,
                loan_pid=loan_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200
    data = get_json(res)
    item_data = data.get('metadata')
    actions = data.get('action_applied')
    assert item_data.get('status') == ItemStatus.ON_SHELF
    assert actions.get(LoanAction.CHECKIN)


def test_items_cancel_request(client, user_librarian_no_email,
                              user_patron_no_email, location, item_type,
                              item_on_shelf, json_header):
    """."""
    login_user_via_session(client, user_librarian_no_email.user)
    item = item_on_shelf
    item_pid = item.pid
    patron_pid = user_patron_no_email.pid

    # request
    res = client.post(
        url_for('api_item.librarian_request'),
        data=json.dumps(
            dict(
                item_pid=item_pid,
                pickup_location_pid=location.pid,
                patron_pid=patron_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200
    data = get_json(res)
    item_data = data.get('metadata')
    actions = data.get('action_applied')
    assert item_data.get('status') == ItemStatus.ON_SHELF
    assert actions.get(LoanAction.REQUEST)
    loan_pid = actions[LoanAction.REQUEST].get('loan_pid')

    # cancel request
    res = client.post(
        url_for('api_item.cancel_loan'),
        data=json.dumps(
            dict(
                item_pid=item_pid,
                loan_pid=loan_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200
    data = get_json(res)
    item_data = data.get('metadata')
    actions = data.get('action_applied')
    assert item_data.get('status') == ItemStatus.ON_SHELF
    assert actions.get(LoanAction.CANCEL)


def test_items_extend(client, user_librarian_no_email,
                      user_patron_no_email, location, item_type,
                      item_on_shelf, json_header,
                      circulation_policies):
    """."""
    login_user_via_session(client, user_librarian_no_email.user)
    item = item_on_shelf
    item_pid = item.pid
    patron_pid = user_patron_no_email.pid

    # checkout
    res = client.post(
        url_for('api_item.checkout'),
        data=json.dumps(
            dict(
                item_pid=item_pid,
                patron_pid=patron_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200
    data = get_json(res)
    actions = data.get('action_applied')
    loan_pid = actions[LoanAction.CHECKOUT].get('loan_pid')
    assert not item.get_extension_count()

    # extend loan
    res = client.post(
        url_for('api_item.extend_loan'),
        data=json.dumps(
            dict(
                item_pid=item_pid,
                loan_pid=loan_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200
    data = get_json(res)
    item_data = data.get('metadata')
    actions = data.get('action_applied')
    assert item_data.get('status') == ItemStatus.ON_LOAN
    assert actions.get(LoanAction.EXTEND)
    assert item.get_extension_count() == 1

    # second extenion
    res = client.post(
        url_for('api_item.extend_loan'),
        data=json.dumps(
            dict(
                item_pid=item_pid,
                loan_pid=loan_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 403

    # checkin
    res = client.post(
        url_for('api_item.checkin'),
        data=json.dumps(
            dict(
                item_pid=item_pid,
                loan_pid=loan_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200


def test_items_lose(client, user_librarian_no_email,
                    user_patron_no_email, location, item_type,
                    item_on_shelf, json_header):
    """."""
    login_user_via_session(client, user_librarian_no_email.user)
    item = item_on_shelf
    item_pid = item.pid
    patron_pid = user_patron_no_email.pid

    # checkout
    res = client.post(
        url_for('api_item.checkout'),
        data=json.dumps(
            dict(
                item_pid=item_pid,
                patron_pid=patron_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200
    # loose item
    res = client.post(
        url_for('api_item.lose'),
        data=json.dumps(
            dict(
                item_pid=item_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200
    data = get_json(res)
    item_data = data.get('metadata')
    actions = data.get('action_applied')
    assert item_data.get('status') == ItemStatus.MISSING
    assert LoanAction.LOSE in actions

    # return missing item
    res = client.post(
        url_for('api_item.return_missing'),
        data=json.dumps(
            dict(
                item_pid=item_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200
    data = get_json(res)
    item_data = data.get('metadata')
    actions = data.get('action_applied')
    assert item_data.get('status') == ItemStatus.ON_SHELF
    assert LoanAction.RETURN_MISSING in actions

    # checkout
    res = client.post(
        url_for('api_item.checkout'),
        data=json.dumps(
            dict(
                item_pid=item_pid,
                patron_pid=patron_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200
    data = get_json(res)
    actions = data.get('action_applied')
    loan_pid = actions[LoanAction.CHECKOUT].get('loan_pid')

    # checkin
    res = client.post(
        url_for('api_item.checkin'),
        data=json.dumps(
            dict(
                item_pid=item_pid,
                loan_pid=loan_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200


def test_items_receive(client, user_librarian_no_email,
                       user_patron_no_email, location, item_type,
                       item_on_shelf, json_header):
    """."""
    login_user_via_session(client, user_librarian_no_email.user)
    item = item_on_shelf
    item_pid = item.pid
    patron_pid = user_patron_no_email.pid
    assert not item.is_loaned_to_patron(user_patron_no_email.get('barcode'))
    # checkout
    res = client.post(
        url_for('api_item.checkout'),
        data=json.dumps(
            dict(
                item_pid=item_pid,
                patron_pid=patron_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200
    data = get_json(res)
    item_data = data.get('metadata')
    actions = data.get('action_applied')
    assert item_data.get('status') == ItemStatus.ON_LOAN
    assert actions.get(LoanAction.CHECKOUT)
    assert item.is_loaned_to_patron(user_patron_no_email.get('barcode'))
    loan_pid = actions[LoanAction.CHECKOUT].get('loan_pid')

    # checkin
    res = client.post(
        url_for('api_item.checkin'),
        data=json.dumps(
            dict(
                item_pid=item_pid,
                loan_pid=loan_pid,
                transaction_location_pid='fake'
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200
    data = get_json(res)
    item_data = data.get('metadata')
    actions = data.get('action_applied')
    assert item_data.get('status') == ItemStatus.IN_TRANSIT
    assert actions.get(LoanAction.CHECKIN)

    # receive
    res = client.post(
        url_for('api_item.receive'),
        data=json.dumps(
            dict(
                item_pid=item_pid,
                loan_pid=loan_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200
    data = get_json(res)
    item_data = data.get('metadata')
    actions = data.get('action_applied')
    assert item_data.get('status') == ItemStatus.ON_SHELF
    assert actions.get(LoanAction.RECEIVE)


def test_items_automatic_checkin(client, user_librarian_no_email,
                                 user_patron_no_email, location, item_type,
                                 item_on_shelf, json_header):
    """."""
    login_user_via_session(client, user_librarian_no_email.user)
    item = item_on_shelf
    item_pid = item.pid
    patron_pid = user_patron_no_email.pid

    # loose item
    res = client.post(
        url_for('api_item.lose'),
        data=json.dumps(
            dict(
                item_pid=item_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200

    # return missing item
    res = client.post(
        url_for('api_item.automatic_checkin'),
        data=json.dumps(
            dict(
                item_barcode=item.get('barcode')
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200
    data = get_json(res)
    item_data = data.get('metadata')
    actions = data.get('action_applied')
    assert item_data.get('status') == ItemStatus.ON_SHELF
    assert LoanAction.RETURN_MISSING in actions

    # checkout
    res = client.post(
        url_for('api_item.checkout'),
        data=json.dumps(
            dict(
                item_pid=item_pid,
                patron_pid=patron_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200
    data = get_json(res)
    actions = data.get('action_applied')
    loan_pid = actions[LoanAction.CHECKOUT].get('loan_pid')

    # checkin
    res = client.post(
        url_for('api_item.checkin'),
        data=json.dumps(
            dict(
                item_pid=item_pid,
                loan_pid=loan_pid,
                transaction_location_pid='fake'
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200

    # receive
    res = client.post(
        url_for('api_item.automatic_checkin'),
        data=json.dumps(
            dict(
                item_barcode=item.get('barcode')
            )
        ),
        content_type='application/json',
    )

    assert res.status_code == 200
    data = get_json(res)
    item_data = data.get('metadata')
    actions = data.get('action_applied')
    assert item_data.get('status') == ItemStatus.ON_SHELF
    assert LoanAction.RECEIVE in actions

    # checkout
    res = client.post(
        url_for('api_item.checkout'),
        data=json.dumps(
            dict(
                item_pid=item_pid,
                patron_pid=patron_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200

    # checkin
    res = client.post(
        url_for('api_item.automatic_checkin'),
        data=json.dumps(
            dict(
                item_barcode=item.get('barcode')
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200
    data = get_json(res)
    item_data = data.get('metadata')
    actions = data.get('action_applied')
    assert item_data.get('status') == ItemStatus.ON_SHELF
    assert LoanAction.CHECKIN in actions


def test_items_no_extend(client, user_librarian_no_email,
                         user_patron_no_email, location, item_type,
                         item_on_shelf, json_header,
                         circ_policy_short):
    """."""
    login_user_via_session(client, user_librarian_no_email.user)
    item = item_on_shelf
    item_pid = item.pid
    patron_pid = user_patron_no_email.pid

    # checkout
    res = client.post(
        url_for('api_item.checkout'),
        data=json.dumps(
            dict(
                item_pid=item_pid,
                patron_pid=patron_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200
    data = get_json(res)
    actions = data.get('action_applied')
    loan_pid = actions[LoanAction.CHECKOUT].get('loan_pid')
    assert not item.get_extension_count()

    circ_policy_short['number_renewals'] = 0

    circ_policy_short.update(
        data=circ_policy_short,
        dbcommit=True,
        reindex=True)
    flush_index(CircPoliciesSearch.Meta.index)

    # extend loan
    res = client.post(
        url_for('api_item.extend_loan'),
        data=json.dumps(
            dict(
                item_pid=item_pid,
                loan_pid=loan_pid
            )
        ),
        content_type='application/json',
    )

    assert res.status_code == 403

    circ_policy_short['number_renewals'] = 1

    circ_policy_short.update(
        data=circ_policy_short,
        dbcommit=True,
        reindex=True)
    flush_index(CircPoliciesSearch.Meta.index)

    # checkin
    res = client.post(
        url_for('api_item.checkin'),
        data=json.dumps(
            dict(
                item_pid=item_pid,
                loan_pid=loan_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200


def test_items_deny_requests(client, user_librarian_no_email,
                             user_patron_no_email, location, item_type,
                             item_on_shelf, json_header, circ_policy_short):
    """."""
    circ_policy_short['allow_requests'] = False
    circ_policy_short.update(
        data=circ_policy_short,
        dbcommit=True,
        reindex=True)
    flush_index(CircPoliciesSearch.Meta.index)
    login_user_via_session(client, user_librarian_no_email.user)
    item = item_on_shelf
    item_pid = item.pid
    patron = user_patron_no_email
    patron_pid = patron.pid

    # request
    res = client.post(
        url_for('api_item.librarian_request'),
        data=json.dumps(
            dict(
                item_pid=item_pid,
                pickup_location_pid=location.pid,
                patron_pid=patron_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 403

    circ_policy_short['allow_requests'] = True
    circ_policy_short.update(
        data=circ_policy_short,
        dbcommit=True,
        reindex=True)
    flush_index(CircPoliciesSearch.Meta.index)
    assert circ_policy_short.get('allow_requests')


def test_extend_possible_actions(client, item_on_shelf,
                                 user_librarian_no_email,
                                 user_patron_no_email,
                                 circ_policy):
    """Extend action changes according to params of cipo"""
    login_user_via_session(client, user_librarian_no_email.user)
    item = item_on_shelf
    patron_pid = user_patron_no_email.pid
    res = client.post(
        url_for('api_item.checkout'),
        data=json.dumps(
            dict(
                item_pid=item.pid,
                patron_pid=patron_pid
            )
        ),
        content_type='application/json',
    )

    res = client.get(
        url_for('api_item.loans', patron_pid=patron_pid)
    )
    assert res.status_code == 200
    data = get_json(res)
    assert data.get('hits').get('total') == 1
    actions = data.get('hits').get('hits')[0].get('item').get('actions')
    assert 'checkin' in actions

    from rero_ils.modules.circ_policies.api import CircPolicy
    circ_policy = CircPolicy.provide_circ_policy(
        item.library_pid,
        'ptty1',
        'itty1'
    )

    circ_policy['number_renewals'] = 0
    circ_policy.update(
        circ_policy,
        dbcommit=True,
        reindex=True
    )
    res = client.get(
        url_for('api_item.loans', patron_pid=patron_pid)
    )
    assert res.status_code == 200
    data = get_json(res)
    assert data.get('hits').get('total') == 1
    actions = data.get('hits').get('hits')[0].get('item').get('actions')
    assert 'extend_loan' not in actions
    assert 'checkin' in actions
    loan_pid = data.get('hits').get('hits')[0].get('loan').get('loan_pid')
    # reset used objects
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

    circ_policy['number_renewals'] = 1
    circ_policy.update(
        circ_policy,
        dbcommit=True,
        reindex=True
    )
    assert circ_policy['number_renewals'] == 1


def test_item_possible_actions(client, item_on_shelf,
                               user_librarian_no_email,
                               user_patron_no_email):
    """Possible action changes according to params of cipo"""
    login_user_via_session(client, user_librarian_no_email.user)
    item = item_on_shelf
    patron_pid = user_patron_no_email.pid
    res = client.get(
        url_for(
            'api_item.item',
            item_barcode=item.get('barcode'),
            patron_pid=patron_pid
        )
    )
    assert res.status_code == 200
    data = get_json(res)

    actions = data.get('metadata').get('item').get('actions')
    assert 'checkout' in actions

    from rero_ils.modules.circ_policies.api import CircPolicy
    circ_policy = CircPolicy.provide_circ_policy(
        item.library_pid,
        'ptty1',
        'itty1'
    )

    circ_policy['allow_checkout'] = False
    circ_policy.update(
        circ_policy,
        dbcommit=True,
        reindex=True
    )
    res = client.get(
        url_for(
            'api_item.item',
            item_barcode=item.get('barcode'),
            patron_pid=patron_pid
        )
    )
    assert res.status_code == 200
    data = get_json(res)

    actions = data.get('metadata').get('item').get('actions')
    assert 'checkout' not in actions

    circ_policy['allow_checkout'] = True
    circ_policy.update(
        circ_policy,
        dbcommit=True,
        reindex=True
    )
    assert circ_policy['allow_checkout']


def test_items_extend_rejected(client, user_librarian_no_email,
                               user_patron_no_email,
                               location, item_type,
                               item_on_shelf, json_header,
                               circ_policy_short):
    """."""
    login_user_via_session(client, user_librarian_no_email.user)
    item = item_on_shelf
    item_pid = item.pid
    patron_pid = user_patron_no_email.pid

    # checkout
    res = client.post(
        url_for('api_item.checkout'),
        data=json.dumps(
            dict(
                item_pid=item_pid,
                patron_pid=patron_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200
    data = get_json(res)
    actions = data.get('action_applied')
    loan_pid = actions[LoanAction.CHECKOUT].get('loan_pid')
    loan = Loan.get_record_by_pid(loan_pid)
    assert not item.get_extension_count()

    max_count = get_extension_params(loan=loan, parameter_name='max_count')

    assert circ_policy_short['number_renewals']
    assert circ_policy_short['renewal_duration'] > 1
    circ_policy_short['renewal_duration'] = 1

    circ_policy_short.update(
        data=circ_policy_short,
        dbcommit=True,
        reindex=True)
    flush_index(CircPoliciesSearch.Meta.index)

    max_count = get_extension_params(loan=loan, parameter_name='max_count')
    assert max_count == 0

    # extend loan rejected
    res = client.post(
        url_for('api_item.extend_loan'),
        data=json.dumps(
            dict(
                item_pid=item_pid,
                loan_pid=loan_pid
            )
        ),
        content_type='application/json',
    )

    assert res.status_code == 403

    circ_policy_short['number_renewals'] = 1
    circ_policy_short['renewal_duration'] = 15

    circ_policy_short.update(
        data=circ_policy_short,
        dbcommit=True,
        reindex=True)
    flush_index(CircPoliciesSearch.Meta.index)

    # checkin
    res = client.post(
        url_for('api_item.checkin'),
        data=json.dumps(
            dict(
                item_pid=item_pid,
                loan_pid=loan_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200


def test_items_extend_end_date(client, user_librarian_no_email,
                               user_patron_no_email,
                               location, item_type,
                               item_on_shelf, json_header,
                               circ_policy_short):
    """."""
    login_user_via_session(client, user_librarian_no_email.user)
    item = item_on_shelf
    item_pid = item.pid
    patron_pid = user_patron_no_email.pid

    # checkout
    res = client.post(
        url_for('api_item.checkout'),
        data=json.dumps(
            dict(
                item_pid=item_pid,
                patron_pid=patron_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200
    data = get_json(res)
    actions = data.get('action_applied')
    loan_pid = actions[LoanAction.CHECKOUT].get('loan_pid')
    loan = Loan.get_record_by_pid(loan_pid)
    assert not item.get_extension_count()

    max_count = get_extension_params(loan=loan, parameter_name='max_count')
    renewal_duration_policy = circ_policy_short['renewal_duration']
    renewal_duration = get_extension_params(
        loan=loan, parameter_name='duration_default')
    assert renewal_duration_policy <= renewal_duration

    # extend loan
    res = client.post(
        url_for('api_item.extend_loan'),
        data=json.dumps(
            dict(
                item_pid=item_pid,
                loan_pid=loan_pid
            )
        ),
        content_type='application/json',
    )

    assert res.status_code == 200
    data = get_json(res)
    actions = data.get('action_applied')
    loan_pid = actions[LoanAction.EXTEND].get('loan_pid')
    loan = Loan.get_record_by_pid(loan_pid)
    end_date = loan.get('end_date')
    current_date = datetime.now()
    calc_date = current_date + timedelta(days=renewal_duration)
    assert (
        calc_date.strftime('%Y-%m-%d') == ciso8601.parse_datetime_as_naive(
            end_date).strftime('%Y-%m-%d')
    )

    # checkin
    res = client.post(
        url_for('api_item.checkin'),
        data=json.dumps(
            dict(
                item_pid=item_pid,
                loan_pid=loan_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200


def test_items_in_transit(client, user_librarian_no_email,
                          user_patron_no_email,
                          location, item_type, store_location,
                          item_on_shelf, json_header,
                          circ_policy):
    """Test item in-transit scenarios."""
    login_user_via_session(client, user_librarian_no_email.user)
    item = item_on_shelf
    item_pid = item.pid
    patron_pid = user_patron_no_email.pid

    # request to pick at another location
    res = client.post(
        url_for('api_item.librarian_request'),
        data=json.dumps(
            dict(
                item_pid=item_pid,
                pickup_location_pid=store_location.pid,
                patron_pid=patron_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200
    data = get_json(res)
    item_data = data.get('metadata')
    actions = data.get('action_applied')
    assert item_data.get('status') == ItemStatus.ON_SHELF
    assert actions.get(LoanAction.REQUEST)
    loan_pid = actions[LoanAction.REQUEST].get('loan_pid')
    item = Item.get_record_by_pid(item_pid)

    # validate (send) request
    res = client.post(
        url_for('api_item.validate_request'),
        data=json.dumps(
            dict(
                item_pid=item_pid,
                loan_pid=loan_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200
    data = get_json(res)
    item_data = data.get('metadata')
    actions = data.get('action_applied')
    assert item_data.get('status') == ItemStatus.IN_TRANSIT
    assert actions.get(LoanAction.VALIDATE)

    # checkout action to req patron is possible without the receive action
    res = client.get(
        url_for(
            'api_item.item',
            item_barcode=item.get('barcode'),
            patron_pid=patron_pid
        )
    )
    assert res.status_code == 200
    data = get_json(res)
    actions = data.get('metadata').get('item').get('actions')
    assert 'checkout' in actions

    # checkout
    res = client.post(
        url_for('api_item.checkout'),
        data=json.dumps(
            dict(
                item_pid=item_pid,
                patron_pid=patron_pid,
                loan_pid=loan_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200
    data = get_json(res)
    assert Item.get_record_by_pid(item_pid).get('status') == ItemStatus.ON_LOAN

    # checkin at location other than item location
    res = client.post(
        url_for('api_item.checkin'),
        data=json.dumps(
            dict(
                item_pid=item_pid,
                loan_pid=loan_pid,
                transaction_location_pid=store_location.pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200
    data = get_json(res)
    item_data = data.get('metadata')
    actions = data.get('action_applied')
    assert item_data.get('status') == ItemStatus.IN_TRANSIT
    assert actions.get(LoanAction.CHECKIN)
    loan_pid = actions[LoanAction.CHECKIN].get('loan_pid')
    loan = actions[LoanAction.CHECKIN]
    assert loan.get('state') == 'ITEM_IN_TRANSIT_TO_HOUSE'

    # a new checkout
    res = client.post(
        url_for('api_item.checkout'),
        data=json.dumps(
            dict(
                item_pid=item_pid,
                patron_pid=patron_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200
    data = get_json(res)
    assert Item.get_record_by_pid(item_pid).get('status') == ItemStatus.ON_LOAN
    actions = data.get('action_applied')
    loan_pid = actions[LoanAction.CHECKOUT].get('loan_pid')

    # checkin at the request location
    res = client.post(
        url_for('api_item.checkin'),
        data=json.dumps(
            dict(
                item_pid=item.pid,
                loan_pid=loan_pid,
                transaction_location_pid=location.pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200


def test_multiple_loans_on_item_error(client, user_librarian_no_email,
                                      user_patron_no_email,
                                      location, item_type, location_21,
                                      item_on_shelf, json_header,
                                      circ_policy,
                                      user_librarian_no_email_specific):
    """Test MultipleLoansOnItemError."""
    login_user_via_session(client, user_librarian_no_email.user)
    item = item_on_shelf
    checked_patron = user_librarian_no_email_specific.pid
    requested_patron = user_patron_no_email.pid

    # checkout to checked_patron
    res = client.post(
        url_for('api_item.checkout'),
        data=json.dumps(
            dict(
                item_pid=item.pid,
                patron_pid=checked_patron,
                transaction_location_pid=location.pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200
    data = get_json(res)
    assert Item.get_record_by_pid(item.pid).get('status') == ItemStatus.ON_LOAN
    item_data = data.get('metadata')
    actions = data.get('action_applied')
    assert item_data.get('status') == ItemStatus.ON_LOAN
    assert actions.get(LoanAction.CHECKOUT)
    loan_pid = actions[LoanAction.CHECKOUT].get('loan_pid')
    item = Item.get_record_by_pid(item.pid)

    # request by requested patron to pick at another location
    res = client.post(
        url_for('api_item.librarian_request'),
        data=json.dumps(
            dict(
                item_pid=item.pid,
                pickup_location_pid=location_21.pid,
                patron_pid=requested_patron
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200
    data = get_json(res)
    item_data = data.get('metadata')
    actions = data.get('action_applied')
    assert item_data.get('status') == ItemStatus.ON_LOAN
    assert actions.get(LoanAction.REQUEST)
    req_loan_pid = actions[LoanAction.REQUEST].get('loan_pid')
    item = Item.get_record_by_pid(item.pid)

    # checkin at the request location
    res = client.post(
        url_for('api_item.checkin'),
        data=json.dumps(
            dict(
                item_pid=item.pid,
                loan_pid=loan_pid,
                transaction_location_pid=location_21.pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200
    data = get_json(res)
    assert Loan.get_record_by_pid(loan_pid).get('state') == 'CANCELLED'
    assert Loan.get_record_by_pid(
        req_loan_pid).get('state') == 'ITEM_IN_TRANSIT_FOR_PICKUP'
    assert Item.get_record_by_pid(item.pid).get('status') == 'in_transit'
    # cancel request
    res = client.post(
        url_for('api_item.cancel_loan'),
        data=json.dumps(
            dict(
                item_pid=item.pid,
                loan_pid=req_loan_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200
