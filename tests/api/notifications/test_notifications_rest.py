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
import pytest
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import VerifyRecordPermissionPatch, flush_index, get_json, \
    postdata, to_relative_url

from rero_ils.modules.api import IlsRecordError
from rero_ils.modules.items.models import ItemStatus
from rero_ils.modules.libraries.api import email_notification_type
from rero_ils.modules.loans.api import Loan, LoanAction, LoanState
from rero_ils.modules.notifications.api import Notification, \
    NotificationsSearch
from rero_ils.modules.notifications.dispatcher import Dispatcher
from rero_ils.modules.notifications.models import NotificationType
from rero_ils.modules.notifications.tasks import process_notifications
from rero_ils.modules.notifications.utils import get_notification
from rero_ils.modules.utils import get_ref_for_pid


def test_availability_notification(
        loan_validated_martigny, item2_lib_martigny,
        mailbox, patron_martigny):
    """Test availability notification created from a loan."""
    mailbox.clear()
    loan = loan_validated_martigny
    assert loan.is_notified(notification_type=NotificationType.AVAILABILITY)
    notification = get_notification(
        loan_validated_martigny,
        notification_type=NotificationType.AVAILABILITY
    )
    assert notification.loan_pid == loan_validated_martigny.get('pid')
    assert notification.item_pid == item2_lib_martigny.pid
    assert notification.patron_pid == patron_martigny.pid

    assert not loan_validated_martigny.is_notified(
        notification_type=NotificationType.RECALL)
    assert not get_notification(
        loan_validated_martigny,
        notification_type=NotificationType.RECALL
    )
    for notification_type in NotificationType.ALL_NOTIFICATIONS:
        process_notifications(notification_type)
    assert len(mailbox)
    mailbox.clear()


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
        librarian_martigny,
        librarian_sion):
    """Test notification filter by organisation."""
    # Martigny
    login_user_via_session(client, librarian_martigny.user)
    list_url = url_for('invenio_records_rest.notif_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total']['value'] == 2

    # Sion
    login_user_via_session(client, librarian_sion.user)
    list_url = url_for('invenio_records_rest.notif_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total']['value'] == 0


def test_notification_secure_api(client, json_header,
                                 librarian_martigny,
                                 librarian_sion,
                                 dummy_notification,
                                 loan_validated_martigny):
    """Test notification secure api create."""
    # Martigny
    login_user_via_session(client, librarian_martigny.user)
    post_entrypoint = 'invenio_records_rest.notif_list'
    item_url = url_for('invenio_records_rest.notif_item', pid_value='notif1')

    # test notification creation
    notif = deepcopy(dummy_notification)
    notif_data = {
        'loan_url': 'https://bib.rero.ch/api/loans/',
        'pid': loan_validated_martigny.get('pid')
    }
    loan_ref = '{loan_url}{pid}'.format(**notif_data)
    notif['context']['loan'] = {"$ref": loan_ref}
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
    login_user_via_session(client, librarian_sion.user)

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

    login_user_via_session(client, librarian_martigny.user)
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
    loan_ref = get_ref_for_pid('loans', loan_validated_martigny.get('pid'))
    record['context']['loan'] = {'$ref': loan_ref}
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
    data = data['metadata']
    data['notification_type'] = NotificationType.DUE_SOON
    res = client.put(
        item_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 200

    # Check that the returned record matches the given data
    data = get_json(res)
    assert data['metadata']['notification_type'] == NotificationType.DUE_SOON

    res = client.get(item_url)
    assert res.status_code == 200

    data = get_json(res)
    assert data['metadata']['notification_type'] == NotificationType.DUE_SOON

    res = client.get(list_url)
    assert res.status_code == 200

    # Delete record/DELETE
    res = client.delete(item_url)
    assert res.status_code == 204

    res = client.get(item_url)
    assert res.status_code == 410

    can, reasons = notif.can_delete
    assert can
    assert reasons == {}

    notif.delete(dbcommit=True, delindex=True)


def test_recall_notification(client, patron_sion, lib_sion,
                             json_header, patron2_martigny,
                             item_lib_sion, librarian_sion,
                             circulation_policies, loc_public_sion,
                             mailbox):
    """Test recall notification."""
    mailbox.clear()
    login_user_via_session(client, librarian_sion.user)
    res, data = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item_lib_sion.pid,
            patron_pid=patron_sion.pid,
            transaction_location_pid=loc_public_sion.pid,
            transaction_user_pid=librarian_sion.pid,
        )
    )
    assert res.status_code == 200
    loan_pid = data.get('action_applied')[LoanAction.CHECKOUT].get('pid')
    loan = Loan.get_record_by_pid(loan_pid)

    assert not loan.is_notified(notification_type=NotificationType.RECALL)
    # test notification permissions
    res, data = postdata(
        client,
        'api_item.librarian_request',
        dict(
            item_pid=item_lib_sion.pid,
            pickup_location_pid=loc_public_sion.pid,
            patron_pid=patron2_martigny.pid,
            transaction_library_pid=lib_sion.pid,
            transaction_user_pid=librarian_sion.pid
        )
    )
    assert res.status_code == 200

    request_loan_pid = data.get(
        'action_applied')[LoanAction.REQUEST].get('pid')
    request_loan = Loan.get_record_by_pid(request_loan_pid)

    flush_index(NotificationsSearch.Meta.index)

    assert loan.is_notified(notification_type=NotificationType.RECALL)
    notification = get_notification(
        loan, notification_type=NotificationType.RECALL)
    assert notification.loan_pid == loan.pid

    assert not loan.is_notified(
        notification_type=NotificationType.AVAILABILITY)
    assert not get_notification(
        loan, notification_type=NotificationType.AVAILABILITY)

    assert not get_notification(
        request_loan, notification_type=NotificationType.REQUEST)
    assert not request_loan.is_notified(
        notification_type=NotificationType.REQUEST)

    assert not len(mailbox)

    for notification_type in NotificationType.ALL_NOTIFICATIONS:
        process_notifications(notification_type)
    # one new email for the patron
    assert mailbox[-1].recipients == [patron_sion.dumps()['email']]

    mailbox.clear()

    # cancel request
    res, _ = postdata(
        client,
        'api_item.cancel_item_request',
        dict(
            item_pid=item_lib_sion.pid,
            pid=request_loan_pid,
            transaction_user_pid=librarian_sion.pid,
            transaction_location_pid=loc_public_sion.pid
        )
    )
    assert res.status_code == 200

    # no new notification is send for the second time
    res, _ = postdata(
        client,
        'api_item.librarian_request',
        dict(
            item_pid=item_lib_sion.pid,
            pickup_location_pid=loc_public_sion.pid,
            patron_pid=patron2_martigny.pid,
            transaction_library_pid=lib_sion.pid,
            transaction_user_pid=librarian_sion.pid
        )
    )
    assert res.status_code == 200

    flush_index(NotificationsSearch.Meta.index)

    assert not loan.is_notified(
        notification_type=NotificationType.RECALL, counter=1)

    assert not loan.is_notified(
        notification_type=NotificationType.AVAILABILITY)
    assert not get_notification(
        loan, notification_type=NotificationType.AVAILABILITY)

    assert not get_notification(
        request_loan, notification_type=NotificationType.REQUEST)
    assert not request_loan.is_notified(
        notification_type=NotificationType.REQUEST)

    assert len(mailbox) == 0


def test_recall_notification_without_email(
        client, patron_sion_without_email1, lib_martigny,
        json_header, patron2_martigny,
        item3_lib_martigny, librarian_martigny,
        circulation_policies, loc_public_martigny,
        mailbox):
    """Test recall notification."""
    mailbox.clear()
    login_user_via_session(client, librarian_martigny.user)
    res, data = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item3_lib_martigny.pid,
            patron_pid=patron_sion_without_email1.pid,
            transaction_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny.pid,
        )
    )
    assert res.status_code == 200
    loan_pid = data.get('action_applied')[LoanAction.CHECKOUT].get('pid')
    loan = Loan.get_record_by_pid(loan_pid)

    assert not loan.is_notified(
        notification_type=NotificationType.RECALL)
    # test notification
    res, data = postdata(
        client,
        'api_item.librarian_request',
        dict(
            item_pid=item3_lib_martigny.pid,
            pickup_location_pid=loc_public_martigny.pid,
            patron_pid=patron2_martigny.pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny.pid
        )
    )
    request_loan_pid = data.get(
        'action_applied')[LoanAction.REQUEST].get('pid')
    assert res.status_code == 200
    flush_index(NotificationsSearch.Meta.index)

    assert loan.is_notified(notification_type=NotificationType.RECALL)
    notification = get_notification(
        loan, notification_type=NotificationType.RECALL)
    assert notification.loan_pid == loan.pid
    assert not loan.is_notified(
        notification_type=NotificationType.AVAILABILITY)
    assert not get_notification(
        loan, notification_type=NotificationType.AVAILABILITY)

    for notification_type in NotificationType.ALL_NOTIFICATIONS:
        process_notifications(notification_type)
    # one new email for the librarian
    assert mailbox[0].recipients == [email_notification_type(
        lib_martigny, notification['notification_type'])]
    # check the address block
    assert patron2_martigny.dumps()['street'] in mailbox[0].body
    mailbox.clear()
    params = {
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    # cancel request
    res, _ = postdata(
        client,
        'api_item.cancel_item_request',
        dict(
            item_pid=item3_lib_martigny.pid,
            pid=request_loan_pid,
            transaction_user_pid=librarian_martigny.pid,
            transaction_library_pid=lib_martigny.pid
        )
    )
    assert res.status_code == 200
    _, actions = item3_lib_martigny.checkin(**params)


def test_recall_notification_with_patron_additional_email_only(
        client, patron_sion_with_additional_email, lib_martigny,
        json_header, patron2_martigny,
        item3_lib_martigny, librarian_martigny,
        circulation_policies, loc_public_martigny,
        mailbox):
    """Test recall notification."""
    mailbox.clear()
    login_user_via_session(client, librarian_martigny.user)
    res, data = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item3_lib_martigny.pid,
            patron_pid=patron_sion_with_additional_email.pid,
            transaction_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny.pid,
        )
    )
    assert res.status_code == 200
    loan_pid = data.get('action_applied')[LoanAction.CHECKOUT].get('pid')
    loan = Loan.get_record_by_pid(loan_pid)

    assert not loan.is_notified(
        notification_type=NotificationType.RECALL)
    # test notification
    res, data = postdata(
        client,
        'api_item.librarian_request',
        dict(
            item_pid=item3_lib_martigny.pid,
            pickup_location_pid=loc_public_martigny.pid,
            patron_pid=patron2_martigny.pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny.pid
        )
    )
    assert res.status_code == 200
    flush_index(NotificationsSearch.Meta.index)

    request_loan_pid = data.get(
        'action_applied')[LoanAction.REQUEST].get('pid')

    assert loan.is_notified(
        notification_type=NotificationType.RECALL)
    notification = get_notification(
        loan, notification_type=NotificationType.RECALL)
    assert notification.loan_pid == loan.pid
    assert not loan.is_notified(
        notification_type=NotificationType.AVAILABILITY)
    assert not get_notification(
        loan, notification_type=NotificationType.AVAILABILITY)

    for notification_type in NotificationType.ALL_NOTIFICATIONS:
        process_notifications(notification_type)
    # one new email for the librarian
    assert mailbox[0].recipients == \
        [patron_sion_with_additional_email[
            'patron']['additional_communication_email']]
    mailbox.clear()
    params = {
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    # cancel request
    res, _ = postdata(
        client,
        'api_item.cancel_item_request',
        dict(
            item_pid=item3_lib_martigny.pid,
            pid=request_loan_pid,
            transaction_user_pid=librarian_martigny.pid,
            transaction_library_pid=lib_martigny.pid
        )
    )
    assert res.status_code == 200
    _, actions = item3_lib_martigny.checkin(**params)


def test_transaction_library_pid(notification_late_martigny,
                                 lib_martigny_data):
    assert notification_late_martigny.transaction_library_pid == \
           lib_martigny_data.get('pid')


def test_notification_templates_list(client, librarian_martigny):
    """Test notification templates list API."""
    url = url_for('notifications.list_available_template')
    res = client.get(url)
    assert res.status_code == 401
    login_user_via_session(client, librarian_martigny.user)
    res = client.get(url)
    assert res.status_code == 200
    data = get_json(res)
    assert isinstance(data.get('templates'), list)


def test_multiple_notifications(client, patron_martigny, patron_sion,
                                lib_martigny, lib_fully,
                                item_lib_martigny, librarian_martigny,
                                loc_public_martigny, circulation_policies,
                                loc_public_fully, mailbox):
    """Test multiple notifications."""
    mailbox.clear()
    login_user_via_session(client, librarian_martigny.user)

    res, data = postdata(
        client,
        'api_item.librarian_request',
        dict(
            item_pid=item_lib_martigny.pid,
            pickup_location_pid=loc_public_martigny.pid,
            patron_pid=patron_martigny.pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny.pid
        )
    )
    assert res.status_code == 200

    request_loan_pid = data.get(
        'action_applied')[LoanAction.REQUEST].get('pid')

    flush_index(NotificationsSearch.Meta.index)

    # REQUEST
    loan = Loan.get_record_by_pid(request_loan_pid)
    assert loan.state == LoanState.PENDING
    assert mailbox[-1].recipients == [
        lib_martigny.get('notification_settings')[4].get('email')]
    mailbox.clear()

    # validate request
    params = {
        'transaction_location_pid': loc_public_fully.pid,
        'transaction_user_pid': librarian_martigny.pid,
        'pid': loan.pid
    }
    item_lib_martigny.validate_request(**params)
    loan = Loan.get_record_by_pid(request_loan_pid)
    assert loan.state == LoanState.ITEM_IN_TRANSIT_FOR_PICKUP

    # TRANSIT NOTICE
    item_lib_martigny.checkout(**params)
    loan = Loan.get_record_by_pid(request_loan_pid)
    assert loan.state == LoanState.ITEM_ON_LOAN

    item_lib_martigny.checkin(**params)
    loan = Loan.get_record_by_pid(request_loan_pid)
    assert loan.state == LoanState.ITEM_IN_TRANSIT_TO_HOUSE
    assert mailbox[-1].recipients == [
        lib_fully.get('notification_settings')[4].get('email')]
    mailbox.clear()

    # back on shelf: required to restore the initial stat for other tests
    params = {
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid,
        'pid': loan.pid
    }
    item_lib_martigny.receive(**params)


def test_request_notifications_temp_item_type(
    client, patron_martigny, patron_sion, lib_martigny, lib_fully,
    item_lib_martigny, librarian_martigny, loc_public_martigny,
    circulation_policies, loc_public_fully, item_type_missing_martigny, mailbox
):
    """Test request notifications with item type with negative availability."""
    mailbox.clear()
    login_user_via_session(client, librarian_martigny.user)
    item_lib_martigny['temporary_item_type'] = {
        '$ref': get_ref_for_pid('itty', item_type_missing_martigny.pid)
    }
    item_lib_martigny.update(item_lib_martigny, dbcommit=True, reindex=True)

    res, data = postdata(
        client,
        'api_item.librarian_request',
        dict(
            item_pid=item_lib_martigny.pid,
            pickup_location_pid=loc_public_fully.pid,
            patron_pid=patron_martigny.pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny.pid
        )
    )
    assert res.status_code == 200

    request_loan_pid = data.get(
        'action_applied')[LoanAction.REQUEST].get('pid')

    flush_index(NotificationsSearch.Meta.index)
    assert len(mailbox) == 0

    # cancel request
    res, _ = postdata(
        client,
        'api_item.cancel_item_request',
        dict(
            item_pid=item_lib_martigny.pid,
            pid=request_loan_pid,
            transaction_user_pid=librarian_martigny.pid,
            transaction_library_pid=lib_martigny.pid
        )
    )
    assert res.status_code == 200
    mailbox.clear()

    del(item_lib_martigny['temporary_item_type'])
    item_lib_martigny.update(item_lib_martigny, dbcommit=True, reindex=True)


def test_request_notifications(client, patron_martigny, patron_sion,
                               lib_martigny,
                               lib_fully,
                               item_lib_martigny, librarian_martigny,
                               loc_public_martigny, circulation_policies,
                               loc_public_fully, mailbox):
    """Test request notifications."""
    mailbox.clear()
    login_user_via_session(client, librarian_martigny.user)

    res, data = postdata(
        client,
        'api_item.librarian_request',
        dict(
            item_pid=item_lib_martigny.pid,
            pickup_location_pid=loc_public_fully.pid,
            patron_pid=patron_martigny.pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny.pid
        )
    )
    assert res.status_code == 200

    request_loan_pid = data.get(
        'action_applied')[LoanAction.REQUEST].get('pid')

    flush_index(NotificationsSearch.Meta.index)
    assert len(mailbox) == 1
    assert mailbox[-1].recipients == [
        lib_martigny.get('notification_settings')[4].get('email')]
    # cancel request
    res, _ = postdata(
        client,
        'api_item.cancel_item_request',
        dict(
            item_pid=item_lib_martigny.pid,
            pid=request_loan_pid,
            transaction_user_pid=librarian_martigny.pid,
            transaction_library_pid=lib_martigny.pid
        )
    )
    assert res.status_code == 200
    mailbox.clear()


@mock.patch.object(Dispatcher, '_process_notification',
                   mock.MagicMock(side_effect=Exception('Test!')))
def test_dispatch_error(client, patron_martigny, patron_sion,
                        lib_martigny,
                        lib_fully,
                        item_lib_martigny, librarian_martigny,
                        loc_public_martigny, circulation_policies,
                        loc_public_fully, mailbox):
    """Test request notifications."""
    mailbox.clear()
    login_user_via_session(client, librarian_martigny.user)

    res, data = postdata(
        client,
        'api_item.librarian_request',
        dict(
            item_pid=item_lib_martigny.pid,
            pickup_location_pid=loc_public_fully.pid,
            patron_pid=patron_martigny.pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny.pid
        )
    )
    assert res.status_code == 200

    request_loan_pid = data.get(
        'action_applied')[LoanAction.REQUEST].get('pid')
    # check that the email has not been sent
    flush_index(NotificationsSearch.Meta.index)
    assert len(mailbox) == 0
    # cancel request
    res, _ = postdata(
        client,
        'api_item.cancel_item_request',
        dict(
            item_pid=item_lib_martigny.pid,
            pid=request_loan_pid,
            transaction_user_pid=librarian_martigny.pid,
            transaction_library_pid=lib_martigny.pid
        )
    )
    assert res.status_code == 200
    mailbox.clear()


def test_multiple_request_booking_notifications(
    client,
    patron_martigny, patron2_martigny, patron4_martigny,
    librarian_martigny, librarian_sion, librarian_saxon,
    loc_public_martigny, loc_public_sion, loc_public_saxon,
    lib_martigny, lib_sion, lib_saxon,
    item_lib_martigny, circulation_policies, mailbox
):
    """Test multiple requests booking notifications."""
    # request 1
    login_user_via_session(client, librarian_martigny.user)
    res, data = postdata(
        client,
        'api_item.librarian_request',
        dict(
            item_pid=item_lib_martigny.pid,
            pickup_location_pid=loc_public_martigny.pid,
            patron_pid=patron_martigny.pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny.pid
        )
    )
    assert res.status_code == 200
    # request 2
    login_user_via_session(client, librarian_sion.user)
    res, data = postdata(
        client,
        'api_item.librarian_request',
        dict(
            item_pid=item_lib_martigny.pid,
            pickup_location_pid=loc_public_sion.pid,
            patron_pid=patron2_martigny.pid,
            transaction_library_pid=lib_sion.pid,
            transaction_user_pid=librarian_sion.pid
        )
    )
    assert res.status_code == 200
    # request 3
    login_user_via_session(client, librarian_saxon.user)
    res, data = postdata(
        client,
        'api_item.librarian_request',
        dict(
            item_pid=item_lib_martigny.pid,
            pickup_location_pid=loc_public_saxon.pid,
            patron_pid=patron4_martigny.pid,
            transaction_library_pid=lib_saxon.pid,
            transaction_user_pid=librarian_saxon.pid
        )
    )
    assert res.status_code == 200

    # checkout for patron1
    params = {
        'patron_pid': patron_martigny.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    loan, actions = item_lib_martigny.checkout(**params)
    assert actions.get(LoanAction.CHECKOUT)
    assert f'Lieu de retrait: {loc_public_martigny.get("code")}'\
        in mailbox[-1].body
    params = {
        'transaction_location_pid': loc_public_sion.pid,
        'transaction_user_pid': librarian_sion.pid
    }
    # checkin at the request pickup of patron2
    _, actions = item_lib_martigny.checkin(**params)
    assert actions.get(LoanAction.CHECKIN)
    assert f'Lieu de retrait: {loc_public_sion.get("code")}'\
        in mailbox[-1].body

    # checkout for patron2
    params = {
        'patron_pid': patron2_martigny.pid,
        'transaction_location_pid': loc_public_sion.pid,
        'transaction_user_pid': librarian_sion.pid
    }
    loan, actions = item_lib_martigny.checkout(**params)
    assert actions.get(LoanAction.CHECKOUT)
    params = {
        'transaction_location_pid': loc_public_saxon.pid,
        'transaction_user_pid': librarian_saxon.pid
    }
    # checkin at the request pickup of patron3
    _, actions = item_lib_martigny.checkin(**params)
    assert actions.get(LoanAction.CHECKIN)
    assert f'Lieu de retrait: {loc_public_saxon.get("code")}'\
        in mailbox[-1].body

    # checkout for patron3
    params = {
        'patron_pid': patron4_martigny.pid,
        'transaction_location_pid': loc_public_saxon.pid,
        'transaction_user_pid': librarian_saxon.pid
    }
    loan, actions = item_lib_martigny.checkout(**params)
    assert actions.get(LoanAction.CHECKOUT)
    params = {
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    # checkin at the request pickup of patron3
    _, actions = item_lib_martigny.checkin(**params)
    assert actions.get(LoanAction.CHECKIN)
    assert item_lib_martigny.status == ItemStatus.ON_SHELF


@mock.patch('flask.current_app.logger.error',
            mock.MagicMock(side_effect=Exception('Test!')))
def test_cancel_notifications(
    client, patron_martigny, lib_martigny, item_lib_martigny,
    librarian_martigny, loc_public_martigny, circulation_policies, mailbox
):
    """Test cancel notifications."""
    login_user_via_session(client, librarian_martigny.user)

    res, data = postdata(
        client,
        'api_item.librarian_request',
        dict(
            item_pid=item_lib_martigny.pid,
            pickup_location_pid=loc_public_martigny.pid,
            patron_pid=patron_martigny.pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny.pid
        )
    )
    assert res.status_code == 200

    request_loan_pid = data.get(
        'action_applied')[LoanAction.REQUEST].get('pid')

    # flush_index(NotificationsSearch.Meta.index)
    res, data = postdata(
        client,
        'api_item.validate_request',
        dict(
            pid=request_loan_pid,
            transaction_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny.pid
        )
    )
    assert res.status_code == 200
    mailbox.clear()
    res, data = postdata(
        client,
        'api_item.checkout',
        dict(
            item_pid=item_lib_martigny.pid,
            patron_pid=patron_martigny.pid,
            transaction_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny.pid,
        )
    )
    assert res.status_code == 200
    loan_pid = data.get(
        'action_applied')[LoanAction.CHECKOUT].get('pid')
    loan = Loan.get_record_by_pid(loan_pid)
    mailbox.clear()
    process_notifications(NotificationType.AVAILABILITY)
    notification = get_notification(loan, NotificationType.AVAILABILITY)
    assert notification['status'] == 'canceled'
    assert len(mailbox) == 0
    # restore to initial state
    res, data = postdata(
        client,
        'api_item.checkin',
        dict(
            item_pid=item_lib_martigny.pid,
            # patron_pid=patron_martigny.pid,
            transaction_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny.pid,
        )
    )
    assert res.status_code == 200
    mailbox.clear()

    # Test REMINDERS notifications.
    #   reminders notification check about the end_date. As the loan end_date
    #   is not yet over, the notification could be cancelled.

    notification = loan.create_notification(_type=NotificationType.DUE_SOON)[0]
    can_cancel, _ = notification.can_be_cancelled()
    assert not can_cancel
    process_notifications(NotificationType.DUE_SOON)
    notification = Notification.get_record_by_pid(notification.pid)
    assert notification['status'] == 'done'
    flush_index(NotificationsSearch.Meta.index)

    # try to create a new DUE_SOON notification for the same loan
    record = {
        'creation_date': datetime.now(timezone.utc).isoformat(),
        'notification_type': NotificationType.DUE_SOON,
        'context': {
            'loan': {'$ref': get_ref_for_pid('loans', loan.pid)},
            'reminder_counter': 0
        }
    }
    notification = Notification.create(record)
    can_cancel, _ = notification.can_be_cancelled()
    assert can_cancel
    Dispatcher.dispatch_notifications([notification.pid])
    notification = Notification.get_record_by_pid(notification.pid)
    assert notification['status'] == 'canceled'


def test_booking_notifications(client, patron_martigny, patron_sion,
                               lib_martigny, lib_fully,
                               librarian_fully,
                               item_lib_martigny, librarian_martigny,
                               loc_public_martigny, circulation_policies,
                               loc_public_fully, mailbox):
    """Test booking notifications."""
    params = {
        'patron_pid': patron_sion.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid
    }
    item_lib_martigny.checkout(**params)
    mailbox.clear()
    login_user_via_session(client, librarian_martigny.user)

    res, data = postdata(
        client,
        'api_item.librarian_request',
        dict(
            item_pid=item_lib_martigny.pid,
            pickup_location_pid=loc_public_martigny.pid,
            patron_pid=patron_martigny.pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny.pid
        )
    )
    assert res.status_code == 200

    request_loan_pid = data.get(
        'action_applied')[LoanAction.REQUEST].get('pid')

    flush_index(NotificationsSearch.Meta.index)

    # BOOKING
    params = {
        'transaction_location_pid': loc_public_fully.pid,
        'transaction_user_pid': librarian_fully.pid
    }
    _, actions = item_lib_martigny.checkin(**params)
    # the checked in loan is canceled and the requested loan is in transit for
    # pickup
    loan = Loan.get_record_by_pid(request_loan_pid)
    assert loan.state == LoanState.ITEM_IN_TRANSIT_FOR_PICKUP
    assert mailbox[0].recipients == [
        lib_fully.get('notification_settings')[4].get('email')]
    # the patron information is the patron request
    assert patron_martigny['patron']['barcode'][0] in mailbox[0].body
    mailbox.clear()


def test_delete_pickup_location(
        loan2_validated_martigny, loc_restricted_martigny, mailbox):
    """Test delete pickup location."""
    mailbox.clear()
    loan = loan2_validated_martigny
    assert loan.is_notified(notification_type=NotificationType.AVAILABILITY)
    notification = get_notification(
        loan,
        notification_type=NotificationType.AVAILABILITY
    )
    assert notification.pickup_location.pid == loc_restricted_martigny.pid
    # We can not delete location used as transaction or pickup location
    # # any more.
    reasons_not_to_delete = loc_restricted_martigny.reasons_not_to_delete()
    assert reasons_not_to_delete == {'links': {'loans': 1}}
    with pytest.raises(IlsRecordError.NotDeleted):
        loc_restricted_martigny.delete(dbcommit=True, delindex=True)
