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

"""Tests REST API notifications."""

import json
from copy import deepcopy

import mock
import pytest
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import VerifyRecordPermissionPatch, flush_index, get_json, \
    to_relative_url

from rero_ils.modules.api import IlsRecordError
from rero_ils.modules.loans.api import Loan, LoanAction
from rero_ils.modules.notifications.api import NotificationsSearch, \
    is_availability_created, is_recalled


def test_notifications_permissions(
        client, notification_availability_martigny, json_header):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.notif_item', pid_value='notif1')
    post_url = url_for('invenio_records_rest.notif_list')

    res = client.get(item_url)
    assert res.status_code == 401

    res = client.post(
        post_url,
        data={},
        headers=json_header
    )
    assert res.status_code == 401

    res = client.put(
        item_url,
        data={},
        headers=json_header
    )

    res = client.delete(item_url)
    assert res.status_code == 401


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_notifications_get(client, notification_availability_martigny):
    """Test record retrieval."""
    record = notification_availability_martigny
    item_url = url_for('invenio_records_rest.notif_item', pid_value=record.pid)
    list_url = url_for(
        'invenio_records_rest.notif_list', q='pid:' + record.pid)
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


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_notifications_post_put_delete(
        client, notification_martigny_data_tmp, json_header):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.notif_item', pid_value='1')
    post_url = url_for('invenio_records_rest.notif_list')
    list_url = url_for('invenio_records_rest.notif_list', q='pid:1')
    record_data = notification_martigny_data_tmp
    # Create record / POST
    record_data['pid'] = '1'
    res = client.post(
        post_url,
        data=json.dumps(record_data),
        headers=json_header
    )
    assert res.status_code == 201

    # Check that the returned record matches the given data
    data = get_json(res)
    assert data['metadata'] == record_data

    res = client.get(item_url)
    assert res.status_code == 200
    data = get_json(res)
    assert record_data == data['metadata']

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


def test_notification_can_delete(
        client, notification_availability_martigny):
    """Test can delete a notification."""
    links = notification_availability_martigny.get_links_to_me()
    assert links == {}

    assert notification_availability_martigny.can_delete

    reasons = notification_availability_martigny.reasons_not_to_delete()
    assert reasons == {}


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
    assert data['hits']['total'] == 2

    # Sion
    login_user_via_session(client, librarian_sion_no_email.user)
    list_url = url_for('invenio_records_rest.notif_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total'] == 0


def test_notification_secure_api(client, json_header,
                                 notification_availability_martigny,
                                 librarian_martigny_no_email,
                                 librarian_sion_no_email):
    """Test notification secure api access."""
    # Martigny
    login_user_via_session(client, librarian_martigny_no_email.user)
    record_url = url_for('invenio_records_rest.notif_item',
                         pid_value=notification_availability_martigny.pid)

    res = client.get(record_url)
    assert res.status_code == 200

    # Sion
    login_user_via_session(client, librarian_sion_no_email.user)
    record_url = url_for('invenio_records_rest.notif_item',
                         pid_value=notification_availability_martigny.pid)

    res = client.get(record_url)
    assert res.status_code == 403


def test_notification_secure_api_create(client, json_header,
                                        librarian_martigny_no_email,
                                        librarian_sion_no_email,
                                        notification_martigny_data):
    """Test notification secure api create."""
    # Martigny
    login_user_via_session(client, librarian_martigny_no_email.user)
    post_url = url_for('invenio_records_rest.notif_list')

    del notification_martigny_data['pid']
    res = client.post(
        post_url,
        data=json.dumps(notification_martigny_data),
        headers=json_header
    )
    assert res.status_code == 201

    # Sion
    login_user_via_session(client, librarian_sion_no_email.user)

    res = client.post(
        post_url,
        data=json.dumps(notification_martigny_data),
        headers=json_header
    )
    assert res.status_code == 403


def test_notification_secure_api_update(client,
                                        librarian_martigny_no_email,
                                        librarian_sion_no_email,
                                        notification_availability_martigny,
                                        json_header):
    """Test notification secure api update."""
    login_user_via_session(client, librarian_martigny_no_email.user)
    record_url = url_for('invenio_records_rest.notif_item',
                         pid_value=notification_availability_martigny.pid)

    data = notification_availability_martigny

    # Sion
    login_user_via_session(client, librarian_sion_no_email.user)

    res = client.put(
        record_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 403


def test_notification_secure_api_delete(
                                    client,
                                    librarian_martigny_no_email,
                                    librarian_sion_no_email,
                                    notification_availability_martigny,
                                    json_header):
    """Test notification secure api delete."""
    login_user_via_session(client, librarian_martigny_no_email.user)
    record_url = url_for('invenio_records_rest.notif_item',
                         pid_value=notification_availability_martigny.pid)
    # Martigny
    res = client.delete(record_url)
    assert res.status_code == 204

    # Sion
    login_user_via_session(client, librarian_sion_no_email.user)

    res = client.delete(record_url)
    assert res.status_code == 410


def test_recall_notification(client, patron_martigny_no_email,
                             patron2_martigny_no_email,
                             item_lib_martigny, librarian_martigny_no_email,
                             circulation_policies, loc_public_martigny):
    """Test recall notification."""
    login_user_via_session(client, librarian_martigny_no_email.user)
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
    data = get_json(res)
    loan_pid = data.get('action_applied')[LoanAction.CHECKOUT].get('loan_pid')
    loan = Loan.get_record_by_pid(loan_pid)

    assert not is_recalled(loan)

    request = client.post(
        url_for('api_item.librarian_request'),
        data=json.dumps(
            dict(
                item_pid=item_lib_martigny.pid,
                pickup_location_pid=loc_public_martigny.pid,
                patron_pid=patron2_martigny_no_email.pid
            )
        ),
        content_type='application/json',
    )
    assert request.status_code == 200
    request_data = get_json(request)
    loan2_pid = request_data.get(
        'action_applied')[LoanAction.REQUEST].get('loan_pid')

    loan2 = Loan.get_record_by_pid(loan2_pid)

    flush_index(NotificationsSearch.Meta.index)

    assert is_recalled(loan)
    assert not is_availability_created(loan2)
    # note, action checkin does automatic validation.
    res = client.post(
        url_for('api_item.checkin'),
        data=json.dumps(
            dict(
                item_pid=item_lib_martigny.pid,
                loan_pid=loan_pid
            )
        ),
        content_type='application/json',
    )
    assert res.status_code == 200
    assert is_recalled(loan)
    assert is_availability_created(loan2)
