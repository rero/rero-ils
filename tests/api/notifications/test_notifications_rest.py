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

"""Tests REST API notifications."""

import json
from copy import deepcopy
from datetime import datetime, timezone

import mock
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import VerifyRecordPermissionPatch, flush_index, get_json, \
    postdata, to_relative_url

from rero_ils.modules.loans.api import Loan, LoanAction
from rero_ils.modules.notifications.api import Notification, \
    NotificationsSearch, get_availability_notification, \
    get_recall_notification


def test_notifications_permissions(
        client, notification_availability_martigny, json_header):
    """Test notification permissions."""

    notif = notification_availability_martigny
    pid = notif.get('pid')
    item_url = url_for('invenio_records_rest.notif_item', pid_value=pid)

    res = client.get(item_url)
    assert res.status_code == 401

    res, _ = postdata(
        client,
        'invenio_records_rest.notif_list',
        {}
    )
    assert res.status_code == 401

    res = client.put(
        item_url,
        data={},
        headers=json_header
    )

    res = client.delete(item_url)
    assert res.status_code == 401


def test_filtered_notifications_get(
        client, notification_availability_martigny,
        librarian_martigny_no_email,
        librarian_sion_no_email):
    """Test notification filter by organisation."""
    # Martigny
    login_user_via_session(client, librarian_martigny_no_email.user)
    list_url = url_for('invenio_records_rest.notif_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total']['value'] == 1

    # Sion
    login_user_via_session(client, librarian_sion_no_email.user)
    list_url = url_for('invenio_records_rest.notif_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total']['value'] == 0


def test_notification_secure_api(client, json_header,
                                 librarian_martigny_no_email,
                                 librarian_sion_no_email,
                                 dummy_notification,
                                 loan_validated_martigny):
    """Test notification secure api create."""
    # Martigny
    login_user_via_session(client, librarian_martigny_no_email.user)
    post_entrypoint = 'invenio_records_rest.notif_list'
    item_url = url_for('invenio_records_rest.notif_item', pid_value='notif1')

    # test notification creation
    notif = deepcopy(dummy_notification)
    notif_data = {
        'loan_url': 'https://ils.rero.ch/api/loans/',
        'pid': loan_validated_martigny.get('pid')
    }
    loan_ref = '{loan_url}{pid}'.format(**notif_data)
    notif['loan'] = {"$ref": loan_ref}
    res, _ = postdata(
        client,
        post_entrypoint,
        notif
    )
    assert res.status_code == 201

    # test get notification
    res = client.get(item_url)
    assert res.status_code == 200
    data = get_json(res)
    assert notif == data['metadata']

    # test notification update
    new_creation_date = datetime.now(timezone.utc).isoformat()
    notif['creation_date'] = new_creation_date
    res = client.put(
        item_url,
        data=json.dumps(notif),
        headers=json_header
    )
    assert res.status_code == 200

    # Sion
    login_user_via_session(client, librarian_sion_no_email.user)

    # test get notification
    res = client.get(item_url)
    assert res.status_code == 403

    res, _ = postdata(
        client,
        post_entrypoint,
        notif
    )
    assert res.status_code == 403

    # test notification update
    new_creation_date = datetime.now(timezone.utc).isoformat()
    notif['creation_date'] = new_creation_date
    res = client.put(
        item_url,
        data=json.dumps(notif),
        headers=json_header
    )
    assert res.status_code == 403

    # test notification delete
    res = client.delete(item_url)
    assert res.status_code == 403

    login_user_via_session(client, librarian_martigny_no_email.user)
    # test notification delete at Martigny
    res = client.delete(item_url)
    assert res.status_code == 204


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_notifications_get(
        client, notification_availability_martigny):
    """Test record retrieval."""
    record = notification_availability_martigny
    pid = record.get('pid')

    item_url = url_for(
        'invenio_records_rest.notif_item', pid_value=pid)
    list_url = url_for(
        'invenio_records_rest.notif_list', q='pid:' + pid)
    item_url_with_resolve = url_for(
        'invenio_records_rest.notif_item',
        pid_value=record.pid,
        resolve=1,
        sources=1
    )

    res = client.get(item_url)
    assert res.status_code == 200

    assert res.headers['ETag'] == '"{}"'.format(record.revision_id)

    data = get_json(res)
    assert record.dumps() == data['metadata']

    # Check metadata
    for k in ['created', 'updated', 'metadata', 'links']:
        assert k in data

    # Check self links
    res = client.get(to_relative_url(data['links']['self']))
    assert res.status_code == 200
    assert data == get_json(res)
    assert record.dumps() == data['metadata']

    # check resolve
    res = client.get(item_url_with_resolve)
    assert res.status_code == 200
    data = get_json(res)
    assert record.replace_refs().dumps() == data['metadata']

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)

    result = data['hits']['hits'][0]['metadata']
    # organisation has been added during the indexing
    del(result['organisation'])
    assert result == record.replace_refs()

    record.delete(dbcommit=True, delindex=True)
    flush_index(NotificationsSearch.Meta.index)


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_notifications_post_put_delete(
        client, dummy_notification, loan_validated_martigny, json_header):
    """Test record delete and update."""

    record = deepcopy(dummy_notification)
    del record['pid']
    notif_data = {
        'loan_url': 'https://ils.rero.ch/api/loans/',
        'pid': loan_validated_martigny.get('pid')
    }
    loan_ref = '{loan_url}{pid}'.format(**notif_data)
    record['loan'] = {"$ref": loan_ref}
    notif = Notification.create(
        record,
        dbcommit=True,
        reindex=True,
        delete_pid=True
    )
    assert notif == record
    flush_index(NotificationsSearch.Meta.index)
    pid = notif.get('pid')

    item_url = url_for('invenio_records_rest.notif_item', pid_value=pid)
    list_url = url_for('invenio_records_rest.notif_list', q='pid:pid')

    new_record = deepcopy(record)

    # Create record / POST
    new_record['pid'] = 'x'
    res, data = postdata(
        client,
        'invenio_records_rest.notif_list',
        new_record
    )
    assert res.status_code == 201

    flush_index(NotificationsSearch.Meta.index)

    # Check that the returned record matches the given data
    assert data['metadata'] == new_record

    res = client.get(item_url)
    assert res.status_code == 200
    data = get_json(res)
    assert notif == data['metadata']

    # Update record/PUT
    data['notification_type'] = 'due_soon'
    res = client.put(
        item_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 200
    # assert res.headers['ETag'] != '"{}"'.format(librarie.revision_id)

    # Check that the returned record matches the given data
    data = get_json(res)
    assert data['metadata']['notification_type'] == 'due_soon'

    res = client.get(item_url)
    assert res.status_code == 200

    data = get_json(res)
    assert data['metadata']['notification_type'] == 'due_soon'

    res = client.get(list_url)
    assert res.status_code == 200

    # Delete record/DELETE
    res = client.delete(item_url)
    assert res.status_code == 204

    res = client.get(item_url)
    assert res.status_code == 410

    links = notif.get_links_to_me()
    assert links == {}

    assert notif.can_delete

    reasons = notif.reasons_not_to_delete()
    assert reasons == {}

    notif.delete(dbcommit=True, delindex=True)


def test_recall_notification(client, patron_martigny_no_email, lib_martigny,
                             json_header, patron2_martigny_no_email,
                             item_lib_martigny, librarian_martigny_no_email,
                             circulation_policies, loc_public_martigny,
                             mailbox):
    """Test recall notification."""
    # process all notifications still in the queue
    Notification.process_notifications()
    mailbox.clear()
    login_user_via_session(client, librarian_martigny_no_email.user)
    res, data = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item_lib_martigny.pid,
            patron_pid=patron_martigny_no_email.pid,
            transaction_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny_no_email.pid,
        )
    )
    assert res.status_code == 200
    loan_pid = data.get('action_applied')[LoanAction.CHECKOUT].get('pid')
    loan = Loan.get_record_by_pid(loan_pid)

    assert not loan.is_notified(notification_type='recall')
    # test notification permissions
    res, data = postdata(
        client,
        'api_item.librarian_request',
        dict(
            item_pid=item_lib_martigny.pid,
            pickup_location_pid=loc_public_martigny.pid,
            patron_pid=patron2_martigny_no_email.pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny_no_email.pid
        )
    )
    assert res.status_code == 200

    request_loan_pid = data.get(
        'action_applied')[LoanAction.REQUEST].get('pid')

    flush_index(NotificationsSearch.Meta.index)

    assert loan.is_notified(notification_type='recall')

    notification = get_recall_notification(loan)
    assert notification.loan_pid == loan.pid

    assert not loan.is_notified(notification_type='availability')
    assert not get_availability_notification(loan)
    assert Notification.process_notifications() == {
        'send': 1, 'reject': 0, 'error': 0}

    # one new email
    assert len(mailbox) == 1
    mailbox.clear()

    # cancel request
    res, _ = postdata(
        client,
        'api_item.cancel_item_request',
        dict(
            item_pid=item_lib_martigny.pid,
            pid=request_loan_pid,
            transaction_user_pid=librarian_martigny_no_email.pid,
            transaction_location_pid=loc_public_martigny.pid
        )
    )
    assert res.status_code == 200

    # no new notification is send for the second time
    res, _ = postdata(
        client,
        'api_item.librarian_request',
        dict(
            item_pid=item_lib_martigny.pid,
            pickup_location_pid=loc_public_martigny.pid,
            patron_pid=patron2_martigny_no_email.pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny_no_email.pid
        )
    )
    assert res.status_code == 200

    flush_index(NotificationsSearch.Meta.index)

    assert loan.is_notified(notification_type='recall')

    notification = get_recall_notification(loan)
    assert notification.loan_pid == loan.pid

    assert not loan.is_notified(notification_type='availability')
    assert not get_availability_notification(loan)
    assert Notification.process_notifications() == {
        'send': 0, 'reject': 0, 'error': 0}
    # no new email
    assert len(mailbox) == 0


def test_recall_notification_without_email(
                              client, patron_sion_without_email, lib_martigny,
                              json_header, patron2_martigny_no_email,
                              item3_lib_martigny, librarian_martigny_no_email,
                              circulation_policies, loc_public_martigny,
                              mailbox):
    """Test recall notification."""
    # process all notifications still in the queue
    Notification.process_notifications()
    mailbox.clear()
    login_user_via_session(client, librarian_martigny_no_email.user)
    res, data = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item3_lib_martigny.pid,
            patron_pid=patron_sion_without_email.pid,
            transaction_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny_no_email.pid,
        )
    )
    assert res.status_code == 200
    loan_pid = data.get('action_applied')[LoanAction.CHECKOUT].get('pid')
    loan = Loan.get_record_by_pid(loan_pid)

    assert not loan.is_notified(notification_type='recall')
    # test notification
    res, data = postdata(
        client,
        'api_item.librarian_request',
        dict(
            item_pid=item3_lib_martigny.pid,
            pickup_location_pid=loc_public_martigny.pid,
            patron_pid=patron2_martigny_no_email.pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny_no_email.pid
        )
    )
    assert res.status_code == 200

    request_loan_pid = data.get(
        'action_applied')[LoanAction.REQUEST].get('pid')

    flush_index(NotificationsSearch.Meta.index)

    assert loan.is_notified(notification_type='recall')

    notification = get_recall_notification(loan)
    assert notification.loan_pid == loan.pid

    assert not loan.is_notified(notification_type='availability')
    assert not get_availability_notification(loan)
    assert Notification.process_notifications() == {
        'send': 1, 'reject': 0, 'error': 0}

    # no email as the patron does not have an email
    assert len(mailbox) == 0
    mailbox.clear()


def test_availability_notification(
        loan_validated_martigny, item2_lib_martigny,
        patron_martigny_no_email):
    """Test availability notification created from a loan."""
    loan = loan_validated_martigny
    assert loan.is_notified(notification_type='availability')
    notification = get_availability_notification(loan_validated_martigny)
    assert notification.loan_pid == loan_validated_martigny.get('pid')
    assert notification.item_pid == item2_lib_martigny.pid
    assert notification.patron_pid == patron_martigny_no_email.pid

    assert not loan_validated_martigny.is_notified(notification_type='recall')
    assert not get_recall_notification(loan_validated_martigny)


def test_transaction_library_pid(notification_overdue_martigny,
                                 lib_martigny_data):
    assert notification_overdue_martigny.transaction_library_pid == \
           lib_martigny_data.get('pid')
