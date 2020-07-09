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

"""Tests REST API items."""

import json
from copy import deepcopy
from datetime import datetime, timezone

import ciso8601
import mock
import pytest
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import VerifyRecordPermissionPatch, check_timezone_date, \
    flush_index, get_json, postdata

from rero_ils.modules.circ_policies.api import CircPoliciesSearch
from rero_ils.modules.errors import RecordValidationError
from rero_ils.modules.items.api import Item
from rero_ils.modules.items.models import ItemNoteTypes, ItemStatus
from rero_ils.modules.loans.api import Loan, LoanAction
from rero_ils.modules.loans.utils import get_extension_params


def test_items_permissions(client, item_lib_martigny,
                           patron_martigny_no_email,
                           json_header):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.item_item', pid_value='item1')

    res = client.get(item_url)
    assert res.status_code == 200

    res, _ = postdata(
        client,
        'invenio_records_rest.item_list',
        {}
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
        'api_item.cancel_item_request',
        'api_item.validate_request',
        'api_item.receive',
        'api_item.return_missing',
        'api_item.extend_loan',
        'api_item.librarian_request'
    ]
    for view in views:
        res, _ = postdata(client, view, {})
        assert res.status_code == 401
    res = client.get(
        url_for('api_item.requested_loans', library_pid='test'),
        data={}
    )
    assert res.status_code == 401
    login_user_via_session(client, patron_martigny_no_email.user)
    for view in views:
        res, _ = postdata(client, view, {})
        assert res.status_code == 403
    res = client.get(
        url_for('api_item.requested_loans', library_pid='test'),
        data={}
    )
    assert res.status_code == 403


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_items_post_put_delete(client, document, loc_public_martigny,
                               item_type_standard_martigny,
                               item_lib_martigny_data, json_header):
    """Test record retrieval."""
    # Create record / POST
    item_url = url_for('invenio_records_rest.item_item', pid_value='1')
    list_url = url_for('invenio_records_rest.item_list', q='pid:1')

    # test when item has no barcode
    item_record_with_no_barcode = deepcopy(item_lib_martigny_data)
    item_record_with_no_barcode['pid'] = 'pid'
    del item_record_with_no_barcode['barcode']
    res, data = postdata(
        client,
        'invenio_records_rest.item_list',
        item_record_with_no_barcode
    )
    assert res.status_code == 201
    item_barcode = data['metadata']['barcode']
    assert item_barcode.startswith('f-')
    # test updating an item with no barcode, keeps the old barcode
    created_item = Item.get_record_by_pid('pid')
    assert created_item.pid == 'pid'
    item_to_update = deepcopy(created_item)
    del item_to_update['barcode']
    updated_item = created_item.update(
        data=item_to_update, dbcommit=True, reindex=True)
    assert updated_item['barcode'].startswith('f-')

    # test replacing an item with no barcode, regenerates a new barcode
    item_to_replace = deepcopy(updated_item)
    del item_to_replace['barcode']
    replaced_item = created_item.replace(
        data=item_to_replace, dbcommit=True, reindex=True)
    assert replaced_item['barcode'].startswith('f-')

    # test when item has a dirty barcode
    item_lib_martigny_data['pid'] = '1'
    item_record_with_dirty_barcode = deepcopy(item_lib_martigny_data)

    item_record_with_dirty_barcode['barcode'] = ' {barcode} '.format(
                barcode=item_record_with_dirty_barcode.get('barcode')
            )
    res, data = postdata(
        client,
        'invenio_records_rest.item_list',
        item_record_with_dirty_barcode
    )
    assert res.status_code == 201

    # Check that the returned record matches the given data
    data['metadata'].pop('available')
    assert data['metadata'] == item_lib_martigny_data

    res = client.get(item_url)
    assert res.status_code == 200

    data = get_json(res)
    data['metadata'].pop('available')
    assert item_lib_martigny_data == data['metadata']

    # Update record/PUT
    data = item_lib_martigny_data
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


def test_checkout_default_policy(client, lib_martigny,
                                 librarian_martigny_no_email,
                                 patron_martigny_no_email,
                                 loc_public_martigny,
                                 item_type_standard_martigny,
                                 item_lib_martigny, json_header,
                                 circulation_policies):
    """Test circ policy parameters"""
    login_user_via_session(client, librarian_martigny_no_email.user)
    item = item_lib_martigny
    item_pid = item.pid
    patron_pid = patron_martigny_no_email.pid

    from rero_ils.modules.circ_policies.api import CircPolicy
    circ_policy = CircPolicy.provide_circ_policy(
        item.library_pid,
        'ptty1',
        'itty1'
    )

    # checkout
    res, data = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item_pid,
            patron_pid=patron_pid,
            transaction_user_pid=librarian_martigny_no_email.pid,
            transaction_location_pid=loc_public_martigny.pid
        )
    )
    assert res.status_code == 200

    actions = data.get('action_applied')
    loan = actions[LoanAction.CHECKOUT]
    end_date = loan.get('end_date')
    start_date = loan.get('start_date')
    checkout_duration = (ciso8601.parse_datetime(
        end_date) - ciso8601.parse_datetime(start_date)).days

    assert checkout_duration >= circ_policy.get('checkout_duration')

    # checkin
    res, _ = postdata(
        client,
        'api_item.checkin',
        dict(
            item_pid=item_pid,
            pid=loan.get('pid'),
            transaction_user_pid=librarian_martigny_no_email.pid,
            transaction_location_pid=loc_public_martigny.pid
        )
    )
    assert res.status_code == 200


def test_checkout_library_level_policy(client, lib_martigny,
                                       librarian_martigny_no_email,
                                       patron_martigny_no_email,
                                       loc_public_martigny,
                                       item_type_standard_martigny,
                                       item_lib_martigny, json_header,
                                       circ_policy_short_martigny):
    """Test circ policy parameters"""
    login_user_via_session(client, librarian_martigny_no_email.user)
    item = item_lib_martigny
    item_pid = item.pid
    patron_pid = patron_martigny_no_email.pid

    # checkout
    res, data = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item_pid,
            patron_pid=patron_pid,
            transaction_user_pid=librarian_martigny_no_email.pid,
            transaction_location_pid=loc_public_martigny.pid
        )
    )
    assert res.status_code == 200

    actions = data.get('action_applied')
    loan = actions[LoanAction.CHECKOUT]
    end_date = loan.get('end_date')
    start_date = loan.get('start_date')
    checkout_duration = (ciso8601.parse_datetime(
        end_date) - ciso8601.parse_datetime(start_date)).days
    assert checkout_duration >= circ_policy_short_martigny.get(
        'checkout_duration')

    # checkin
    res, _ = postdata(
        client,
        'api_item.checkin',
        dict(
            item_pid=item_pid,
            pid=loan.get('pid'),
            transaction_user_pid=librarian_martigny_no_email.pid,
            transaction_location_pid=loc_public_martigny.pid
        )
    )
    assert res.status_code == 200


def test_checkout_organisation_policy(client, lib_martigny,
                                      librarian_martigny_no_email,
                                      patron_martigny_no_email,
                                      loc_public_martigny,
                                      item_type_standard_martigny,
                                      item_lib_martigny, json_header,
                                      circ_policy_short_martigny):
    """Test circ policy parameters"""
    login_user_via_session(client, librarian_martigny_no_email.user)
    item = item_lib_martigny
    item_pid = item.pid
    patron_pid = patron_martigny_no_email.pid

    # checkout
    res, data = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item_pid,
            patron_pid=patron_pid,
            transaction_user_pid=librarian_martigny_no_email.pid,
            transaction_location_pid=loc_public_martigny.pid
        )
    )
    assert res.status_code == 200

    actions = data.get('action_applied')
    loan = actions[LoanAction.CHECKOUT]
    end_date = loan.get('end_date')
    start_date = loan.get('start_date')
    checkout_duration = (ciso8601.parse_datetime(
        end_date) - ciso8601.parse_datetime(start_date)).days
    assert checkout_duration >= circ_policy_short_martigny.get(
        'checkout_duration')

    # checkin
    res, _ = postdata(
        client,
        'api_item.checkin',
        dict(
            item_pid=item_pid,
            pid=loan.get('pid'),
            transaction_user_pid=librarian_martigny_no_email.pid,
            transaction_location_pid=loc_public_martigny.pid
        )
    )
    assert res.status_code == 200


def test_items_receive(client, librarian_martigny_no_email,
                       patron_martigny_no_email, loc_public_martigny,
                       item_type_standard_martigny,
                       item_lib_martigny, json_header,
                       circulation_policies):
    """Test item receive."""
    login_user_via_session(client, librarian_martigny_no_email.user)
    item = item_lib_martigny
    item_pid = item.pid
    patron_pid = patron_martigny_no_email.pid
    assert not item.is_loaned_to_patron(patron_martigny_no_email.get(
        'barcode'))
    location = loc_public_martigny
    # checkout
    res, data = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item_pid,
            patron_pid=patron_pid,
            transaction_user_pid=librarian_martigny_no_email.pid,
            transaction_location_pid=loc_public_martigny.pid
        )
    )
    assert res.status_code == 200
    item_data = data.get('metadata')
    actions = data.get('action_applied')
    assert item_data.get('status') == ItemStatus.ON_LOAN
    assert actions.get(LoanAction.CHECKOUT)
    assert item.is_loaned_to_patron(patron_martigny_no_email.get('barcode'))
    loan_pid = actions[LoanAction.CHECKOUT].get('pid')

    # checkin
    res, data = postdata(
        client,
        'api_item.checkin',
        dict(
            item_pid=item_pid,
            pid=loan_pid,
            transaction_location_pid='fake',
            transaction_user_pid=librarian_martigny_no_email.pid,
        )
    )
    assert res.status_code == 200
    item_data = data.get('metadata')
    actions = data.get('action_applied')
    assert item_data.get('status') == ItemStatus.IN_TRANSIT
    assert actions.get(LoanAction.CHECKIN)

    # receive
    res, data = postdata(
        client,
        'api_item.receive',
        dict(
            item_pid=item_pid,
            pid=loan_pid,
            transaction_user_pid=librarian_martigny_no_email.pid,
            transaction_location_pid=loc_public_martigny.pid
        )
    )
    assert res.status_code == 200
    item_data = data.get('metadata')
    actions = data.get('action_applied')
    assert item_data.get('status') == ItemStatus.ON_SHELF
    assert actions.get(LoanAction.RECEIVE)


def test_items_no_extend(client, librarian_martigny_no_email,
                         patron_martigny_no_email, loc_public_martigny,
                         item_type_standard_martigny,
                         item_lib_martigny, json_header,
                         circ_policy_short_martigny):
    """Test items when no renewals is possible."""
    login_user_via_session(client, librarian_martigny_no_email.user)
    item = item_lib_martigny
    item_pid = item.pid
    patron_pid = patron_martigny_no_email.pid
    location = loc_public_martigny

    # checkout
    res, data = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item_pid,
            patron_pid=patron_pid,
            transaction_user_pid=librarian_martigny_no_email.pid,
            transaction_location_pid=loc_public_martigny.pid
        )
    )
    assert res.status_code == 200
    actions = data.get('action_applied')
    loan_pid = actions[LoanAction.CHECKOUT].get('pid')
    assert not item.get_extension_count()

    circ_policy_short_martigny['number_renewals'] = 0

    circ_policy_short_martigny.update(
        data=circ_policy_short_martigny,
        dbcommit=True,
        reindex=True)
    flush_index(CircPoliciesSearch.Meta.index)

    # extend loan
    res, _ = postdata(
        client,
        'api_item.extend_loan',
        dict(
            item_pid=item_pid,
            pid=loan_pid,
            transaction_user_pid=librarian_martigny_no_email.pid,
            transaction_location_pid=loc_public_martigny.pid
        )
    )

    assert res.status_code == 403

    circ_policy_short_martigny['number_renewals'] = 1

    circ_policy_short_martigny.update(
        data=circ_policy_short_martigny,
        dbcommit=True,
        reindex=True)
    flush_index(CircPoliciesSearch.Meta.index)

    # checkin
    res, _ = postdata(
        client,
        'api_item.checkin',
        dict(
            item_pid=item_pid,
            pid=loan_pid,
            transaction_user_pid=librarian_martigny_no_email.pid,
            transaction_location_pid=loc_public_martigny.pid
        )
    )
    assert res.status_code == 200


def test_items_deny_requests(client, librarian_martigny_no_email,
                             patron_martigny_no_email, loc_public_martigny,
                             item_type_standard_martigny, lib_martigny,
                             item_lib_martigny, json_header,
                             circ_policy_short_martigny):
    """Test items when requests are denied."""
    location = loc_public_martigny
    circ_policy_short_martigny['allow_requests'] = False
    circ_policy_short_martigny.update(
        data=circ_policy_short_martigny,
        dbcommit=True,
        reindex=True)
    flush_index(CircPoliciesSearch.Meta.index)
    login_user_via_session(client, librarian_martigny_no_email.user)
    item = item_lib_martigny
    item_pid = item.pid
    patron = patron_martigny_no_email
    patron_pid = patron.pid

    # request
    res, _ = postdata(
        client,
        'api_item.librarian_request',
        dict(
            item_pid=item_pid,
            pickup_location_pid=location.pid,
            patron_pid=patron_pid,
            transaction_user_pid=librarian_martigny_no_email.pid,
            transaction_location_pid=loc_public_martigny.pid
        )
    )
    assert res.status_code == 403

    # test can request because of a circulation policy does not allow request
    res = client.get(
        url_for(
            'api_item.can_request',
            item_pid=item_pid,
            library_pid=lib_martigny.pid,
            patron_barcode=patron.get('barcode')
        )
    )
    assert res.status_code == 200
    data = get_json(res)
    assert not data.get('can_request')

    circ_policy_short_martigny['allow_requests'] = True
    circ_policy_short_martigny.update(
        data=circ_policy_short_martigny,
        dbcommit=True,
        reindex=True)
    flush_index(CircPoliciesSearch.Meta.index)
    assert circ_policy_short_martigny.get('allow_requests')


def test_extend_possible_actions(client, item_lib_martigny,
                                 loc_public_martigny,
                                 librarian_martigny_no_email,
                                 patron_martigny_no_email,
                                 circ_policy_short_martigny):
    """Extend action changes according to params of cipo."""
    login_user_via_session(client, librarian_martigny_no_email.user)
    circ_policy = circ_policy_short_martigny
    item = item_lib_martigny
    patron_pid = patron_martigny_no_email.pid
    res, _ = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item.pid,
            patron_pid=patron_pid,
            transaction_user_pid=librarian_martigny_no_email.pid,
            transaction_location_pid=loc_public_martigny.pid
        )
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
    loan_pid = data.get('hits').get('hits')[0].get('loan').get('pid')
    # reset used objects
    res, _ = postdata(
        client,
        'api_item.checkin',
        dict(
            item_pid=item.pid,
            pid=loan_pid,
            transaction_user_pid=librarian_martigny_no_email.pid,
            transaction_location_pid=loc_public_martigny.pid
        )
    )
    assert res.status_code == 200

    circ_policy['number_renewals'] = 1
    circ_policy.update(
        circ_policy,
        dbcommit=True,
        reindex=True
    )
    assert circ_policy['number_renewals'] == 1


def test_items_extend_end_date(client, librarian_martigny_no_email,
                               patron_martigny_no_email,
                               loc_public_martigny,
                               item_type_standard_martigny,
                               item_lib_martigny, json_header,
                               circ_policy_short_martigny):
    """Test correct renewal due date for items."""
    login_user_via_session(client, librarian_martigny_no_email.user)
    item = item_lib_martigny
    item_pid = item.pid
    patron_pid = patron_martigny_no_email.pid

    # checkout
    res, data = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item_pid,
            patron_pid=patron_pid,
            transaction_user_pid=librarian_martigny_no_email.pid,
            transaction_location_pid=loc_public_martigny.pid
        )
    )
    assert res.status_code == 200
    actions = data.get('action_applied')
    loan_pid = actions[LoanAction.CHECKOUT].get('pid')
    loan = Loan.get_record_by_pid(loan_pid)
    assert not item.get_extension_count()

    max_count = get_extension_params(loan=loan, parameter_name='max_count')
    renewal_duration_policy = circ_policy_short_martigny['renewal_duration']
    renewal_duration = get_extension_params(
        loan=loan, parameter_name='duration_default')
    assert renewal_duration_policy <= renewal_duration.days

    # extend loan
    res, data = postdata(
        client,
        'api_item.extend_loan',
        dict(
            item_pid=item_pid,
            pid=loan_pid,
            transaction_user_pid=librarian_martigny_no_email.pid,
            transaction_location_pid=loc_public_martigny.pid
        )
    )

    assert res.status_code == 200

    # Compare expected loan date with processed one
    # first get loan UTC date
    actions = data.get('action_applied')
    loan_pid = actions[LoanAction.EXTEND].get('pid')
    loan = Loan.get_record_by_pid(loan_pid)
    loan_date = loan.get('end_date')
    # then process a date with current UTC date + renewal
    current_date = datetime.now(timezone.utc)
    calc_date = current_date + renewal_duration
    # finally the comparison should give the same date (in UTC)!
    assert (
        calc_date.strftime('%Y-%m-%d') == ciso8601.parse_datetime(
            loan_date).astimezone(timezone.utc).strftime('%Y-%m-%d')
    )

    # checkin
    res, _ = postdata(
        client,
        'api_item.checkin',
        dict(
            item_pid=item_pid,
            pid=loan_pid,
            transaction_user_pid=librarian_martigny_no_email.pid,
            transaction_location_pid=loc_public_martigny.pid
        )
    )
    assert res.status_code == 200


def test_multiple_loans_on_item_error(client,
                                      patron_martigny_no_email,
                                      patron2_martigny_no_email,
                                      loc_public_martigny,
                                      item_type_standard_martigny,
                                      item_lib_martigny, json_header,
                                      circulation_policies,
                                      loc_public_fully,
                                      librarian_martigny_no_email):
    """Test MultipleLoansOnItemError."""
    login_user_via_session(client, librarian_martigny_no_email.user)
    item = item_lib_martigny
    checked_patron = patron2_martigny_no_email.pid
    requested_patron = patron_martigny_no_email.pid
    location = loc_public_martigny
    # checkout to checked_patron
    res, data = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item.pid,
            patron_pid=checked_patron,
            transaction_location_pid=location.pid,
            transaction_user_pid=librarian_martigny_no_email.pid
        )
    )
    assert res.status_code == 200
    assert Item.get_record_by_pid(item.pid).get('status') == ItemStatus.ON_LOAN
    item_data = data.get('metadata')
    actions = data.get('action_applied')
    assert item_data.get('status') == ItemStatus.ON_LOAN
    assert actions.get(LoanAction.CHECKOUT)
    loan_pid = actions[LoanAction.CHECKOUT].get('pid')
    item = Item.get_record_by_pid(item.pid)

    # request by requested patron to pick at another location
    res, data = postdata(
        client,
        'api_item.librarian_request',
        dict(
            item_pid=item.pid,
            pickup_location_pid=loc_public_fully.pid,
            patron_pid=requested_patron,
            transaction_user_pid=librarian_martigny_no_email.pid,
            transaction_location_pid=loc_public_martigny.pid
        )
    )
    assert res.status_code == 200
    item_data = data.get('metadata')
    actions = data.get('action_applied')
    assert item_data.get('status') == ItemStatus.ON_LOAN
    assert actions.get(LoanAction.REQUEST)
    req_loan_pid = actions[LoanAction.REQUEST].get('pid')
    item = Item.get_record_by_pid(item.pid)

    # checkin at the request location
    res, data = postdata(
        client,
        'api_item.checkin',
        dict(
            item_pid=item.pid,
            pid=loan_pid,
            transaction_location_pid=loc_public_fully.pid,
            transaction_user_pid=librarian_martigny_no_email.pid
        )
    )
    assert res.status_code == 200
    # test the returned three actions
    loans = data.get('action_applied')
    checked_in_loan = loans.get(LoanAction.CHECKIN)
    cancelled_loan = loans.get(LoanAction.CANCEL)
    validated_loan = loans.get(LoanAction.VALIDATE)
    assert checked_in_loan.get('pid') == cancelled_loan.get('pid')
    assert validated_loan.get('pid') == req_loan_pid

    assert Loan.get_record_by_pid(loan_pid).get('state') == 'CANCELLED'
    new_loan = Loan.get_record_by_pid(req_loan_pid)
    assert new_loan.get('state') == 'ITEM_AT_DESK'
    assert Item.get_record_by_pid(item.pid).get('status') == \
        ItemStatus.AT_DESK
    # cancel request
    res, _ = postdata(
        client,
        'api_item.cancel_item_request',
        dict(
            item_pid=item.pid,
            pid=req_loan_pid,
            transaction_user_pid=librarian_martigny_no_email.pid,
            transaction_location_pid=loc_public_martigny.pid
        )
    )
    assert res.status_code == 200


def test_filtered_items_get(
        client, librarian_martigny_no_email, item_lib_martigny,
        item_lib_saxon, item_lib_fully,
        librarian_sion_no_email, item_lib_sion):
    """Test items filter by organisation."""
    # Martigny
    login_user_via_session(client, librarian_martigny_no_email.user)
    list_url = url_for('invenio_records_rest.item_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total'] == 4

    # Sion
    login_user_via_session(client, librarian_sion_no_email.user)
    list_url = url_for('invenio_records_rest.item_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total'] == 1


def test_items_notes(client, librarian_martigny_no_email, item_lib_martigny,
                     json_header):
    """Test items notes."""

    item = item_lib_martigny
    login_user_via_session(client, librarian_martigny_no_email.user)

    # at start the items have one note
    assert len(item.notes) == 1

    # set one public & one staff note
    item['notes'] = [
        {'type': ItemNoteTypes.PUBLIC, 'content': 'Public note'},
        {'type': ItemNoteTypes.STAFF, 'content': 'Staff note'}
    ]
    res = client.put(
        url_for('invenio_records_rest.item_item', pid_value=item.pid),
        data=json.dumps(item),
        headers=json_header
    )
    assert res.status_code == 200

    # add a second public note -- This should fail because we can only have one
    # note of each type for an item
    item['notes'].append(
        {'type': ItemNoteTypes.PUBLIC, 'content': 'Second public note'}
    )
    with pytest.raises(RecordValidationError):
        client.put(
            url_for('invenio_records_rest.item_item', pid_value=item.pid),
            data=json.dumps(item),
            headers=json_header
        )
    item['notes'] = item.notes[:-1]

    # get a specific type of notes
    #  --> public : should return a note
    #  --> checkin : should return nothing
    #  --> dummy : should never return something !
    assert item.get_note(ItemNoteTypes.PUBLIC)
    assert item.get_note(ItemNoteTypes.CHECKIN) is None
    assert item.get_note('dummy') is None


def test_pending_loans_order(client, librarian_martigny_no_email,
                             patron_martigny_no_email, loc_public_martigny,
                             item_type_standard_martigny,
                             item2_lib_martigny, json_header,
                             patron2_martigny_no_email, patron_sion_no_email,
                             circulation_policies):
    """Test sort of pending loans."""
    login_user_via_session(client, librarian_martigny_no_email.user)
    library_pid = librarian_martigny_no_email.replace_refs()['library']['pid']

    res, _ = postdata(
        client,
        'api_item.librarian_request',
        dict(
            item_pid=item2_lib_martigny.pid,
            patron_pid=patron_sion_no_email.pid,
            pickup_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny_no_email.pid,
            transaction_location_pid=loc_public_martigny.pid
        )
    )

    res, _ = postdata(
        client,
        'api_item.librarian_request',
        dict(
            item_pid=item2_lib_martigny.pid,
            patron_pid=patron_martigny_no_email.pid,
            pickup_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny_no_email.pid,
            transaction_location_pid=loc_public_martigny.pid
        )
    )
    assert res.status_code == 200

    res, _ = postdata(
        client,
        'api_item.librarian_request',
        dict(
            item_pid=item2_lib_martigny.pid,
            patron_pid=patron2_martigny_no_email.pid,
            pickup_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny_no_email.pid,
            transaction_location_pid=loc_public_martigny.pid
        )
    )
    assert res.status_code == 200

    # sort by pid asc
    res = client.get(
        url_for(
            'api_item.requested_loans', library_pid=library_pid,
            sort='pid'))
    assert res.status_code == 200
    data = get_json(res)
    loans = data['hits']['hits'][0]['item']['pending_loans']
    assert loans[2]['pid'] > loans[1]['pid'] > loans[0]['pid']

    # sort by pid desc
    res = client.get(
        url_for(
            'api_item.requested_loans', library_pid=library_pid,
            sort='-pid'))
    assert res.status_code == 200
    data = get_json(res)
    loans = data['hits']['hits'][0]['item']['pending_loans']
    assert loans[2]['pid'] < loans[1]['pid'] < loans[0]['pid']

    # sort by transaction desc
    res = client.get(
        url_for(
            'api_item.requested_loans', library_pid=library_pid,
            sort='-transaction_date'))
    assert res.status_code == 200
    data = get_json(res)
    loans = data['hits']['hits'][0]['item']['pending_loans']
    assert loans[2]['pid'] < loans[1]['pid'] < loans[0]['pid']

    # sort by patron_pid asc
    res = client.get(
        url_for(
            'api_item.requested_loans', library_pid=library_pid,
            sort='patron_pid'))
    assert res.status_code == 200
    data = get_json(res)
    loans = data['hits']['hits'][0]['item']['pending_loans']
    assert loans[0]['patron_pid'] == patron_sion_no_email.pid
    assert loans[1]['patron_pid'] == patron_martigny_no_email.pid
    assert loans[2]['patron_pid'] == patron2_martigny_no_email.pid

    # sort by invalid field
    res = client.get(
        url_for(
            'api_item.requested_loans', library_pid=library_pid,
            sort='does not exist'))
    assert res.status_code == 500
    data = get_json(res)
    assert 'RequestError(400' in data['status']


def test_item_possible_actions(client, item_lib_martigny,
                               librarian_martigny_no_email,
                               patron_martigny_no_email,
                               circulation_policies):
    """Possible action changes according to params of cipo."""
    login_user_via_session(client, librarian_martigny_no_email.user)
    item = item_lib_martigny
    patron_pid = patron_martigny_no_email.pid
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
