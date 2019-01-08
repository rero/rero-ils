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

import mock
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import VerifyRecordPermissionPatch, get_json

from rero_ils.modules.items.api import Item, ItemStatus
from rero_ils.modules.loans.api import LoanAction


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
    assert res.status_code == 500

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
    assert res.status_code == 500


def test_items_simple_loan(client, user_librarian_no_email,
                           user_patron_no_email, location, item_type,
                           item_on_shelf, json_header):
    """."""
    login_user_via_session(client, user_librarian_no_email.user)
    item = item_on_shelf
    item_pid = item.pid
    patron_pid = user_patron_no_email.pid
    assert not item.is_loaned_to_patron(user_patron_no_email.get('barcode'))
    assert item.can_delete
    assert item.available
    # document_item_url = url_for(
    # 'invenio_records_rest.doc_item', pid_value='1')
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
