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
from invenio_circulation.search.api import LoansSearch
from utils import VerifyRecordPermissionPatch, flush_index, get_json, \
    to_relative_url

from rero_ils.modules.api import IlsRecordError
from rero_ils.modules.loans.api import Loan, LoanAction
from rero_ils.modules.notifications.api import Notification, \
    NotificationsSearch, get_recall_notification


def test_notifications_permissions(client, db, es, dummy_notification,
                                   loan_validated, json_header):
    """Test notification permissions."""

    record = deepcopy(dummy_notification)
    del record['pid']
    data = {
        'loan_url': 'https://ils.rero.ch/api/loans/',
        'pid': loan_validated.get('loan_pid')
    }
    loan_ref = '{loan_url}{pid}'.format(**data)
    record['loan'] = {"$ref": loan_ref}
    notif = Notification.create(
        record,
        dbcommit=True,
        reindex=True,
        delete_pid=True
    )
    assert notif == record
    assert notif.get('pid') == '1'

    flush_index(NotificationsSearch.Meta.index)

    pid = notif.get('pid')
    item_url = url_for('invenio_records_rest.notif_item', pid_value=pid)
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

    notif.delete(dbcommit=True, delindex=True)
    flush_index(NotificationsSearch.Meta.index)


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_notifications_get(client, dummy_notification, loan_validated):
    """Test record retrieval."""
    del dummy_notification['pid']
    data = {
        'loan_url': 'https://ils.rero.ch/api/loans/',
        'pid': loan_validated.get('loan_pid')
    }
    loan_ref = '{loan_url}{pid}'.format(**data)
    dummy_notification['loan'] = {"$ref": loan_ref}
    record = Notification.create(
        dummy_notification,
        dbcommit=True,
        reindex=True,
        delete_pid=True
    )
    assert record == dummy_notification
    assert record.get('pid') == '1'

    flush_index(NotificationsSearch.Meta.index)

    pid = record.get('pid')

    item_url = url_for(
          'invenio_records_rest.notif_item', pid_value=record.pid)
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

    record.delete(dbcommit=True, delindex=True)
    flush_index(NotificationsSearch.Meta.index)


# @mock.patch('invenio_records_rest.views.verify_record_permission',
#             mock.MagicMock(return_value=VerifyRecordPermissionPatch))
# def test_notifications_post_put_delete(
#         client, dummy_notification, loan_validated, json_header):
#     """Test record delete and update."""

#     record = deepcopy(dummy_notification)
#     del record['pid']
#     notif_data = {
#         'loan_url': 'https://ils.rero.ch/api/loans/',
#         'pid': loan_validated.get('loan_pid')
#     }
#     loan_ref = '{loan_url}{pid}'.format(**notif_data)
#     record['loan'] = {"$ref": loan_ref}
#     notif = Notification.create(
#         record,
#         dbcommit=True,
#         reindex=True,
#         delete_pid=True
#     )
#     assert notif == record
#     flush_index(NotificationsSearch.Meta.index)
#     pid = notif.get('pid')

#     item_url = url_for('invenio_records_rest.notif_item', pid_value=pid)
#     post_url = url_for('invenio_records_rest.notif_list')
#     list_url = url_for('invenio_records_rest.notif_list', q='pid:pid')

#     new_record = deepcopy(record)

#     # Create record / POST
#     new_record['pid'] = 'x'
#     res = client.post(
#         post_url,
#         data=json.dumps(new_record),
#         headers=json_header
#     )
#     assert res.status_code == 201

#     flush_index(NotificationsSearch.Meta.index)

#     # Check that the returned record matches the given data
#     data = get_json(res)
#     assert data['metadata'] == new_record

#     res = client.get(item_url)
#     assert res.status_code == 200
#     data = get_json(res)
#     assert notif == data['metadata']

#     # Update record/PUT
#     data['notification_type'] = 'due_soon'
#     res = client.put(
#         item_url,
#         data=json.dumps(data),
#         headers=json_header
#     )
#     assert res.status_code == 200
#     # assert res.headers['ETag'] != '"{}"'.format(librarie.revision_id)

#     # Check that the returned record matches the given data
#     data = get_json(res)
#     assert data['metadata']['notification_type'] == 'due_soon'

#     res = client.get(item_url)
#     assert res.status_code == 200

#     data = get_json(res)
#     assert data['metadata']['notification_type'] == 'due_soon'

#     res = client.get(list_url)
#     assert res.status_code == 200

#     # Delete record/DELETE
#     res = client.delete(item_url)
#     assert res.status_code == 204

#     res = client.get(item_url)
#     assert res.status_code == 410

#     links = notif.get_links_to_me()
#     assert links == {}

#     assert notif.can_delete

#     reasons = notif.reasons_not_to_delete()
#     assert reasons == {}

#     notif.delete(dbcommit=True, delindex=True)

# def test_filtered_notifications_get(
#         client, notification_availabilty_martigny,
#         librarian_martigny_no_email,
#         librarian_sion_no_email):
#     """Test notification filter by organisation."""
#     # Martigny
#     login_user_via_session(client, librarian_martigny_no_email.user)
#     list_url = url_for('invenio_records_rest.notif_list')

#     res = client.get(list_url)
#     assert res.status_code == 200
#     data = get_json(res)
#     assert data['hits']['total'] == 2

#     # Sion
#     login_user_via_session(client, librarian_sion_no_email.user)
#     list_url = url_for('invenio_records_rest.notif_list')

#     res = client.get(list_url)
#     assert res.status_code == 200
#     data = get_json(res)
#     assert data['hits']['total'] == 0


# def test_notification_secure_api(client, json_header,
#                                  notification_availabilty_martigny,
#                                  librarian_martigny_no_email,
#                                  librarian_sion_no_email):
#     """Test notification secure api access."""
#     # Martigny
#     login_user_via_session(client, librarian_martigny_no_email.user)
#     record_url = url_for('invenio_records_rest.notif_item',
#                          pid_value=notification_availabilty_martigny.pid)

#     res = client.get(record_url)
#     assert res.status_code == 200

#     # Sion
#     login_user_via_session(client, librarian_sion_no_email.user)
#     record_url = url_for('invenio_records_rest.notif_item',
#                          pid_value=notification_availabilty_martigny.pid)

#     res = client.get(record_url)
#     assert res.status_code == 403


# def test_notification_secure_api_create(client, json_header,
#                                         librarian_martigny_no_email,
#                                         librarian_sion_no_email,
#                                         notification_martigny_data):
#     """Test notification secure api create."""
#     # Martigny
#     login_user_via_session(client, librarian_martigny_no_email.user)
#     post_url = url_for('invenio_records_rest.notif_list')

#     del notification_martigny_data['pid']
#     res = client.post(
#         post_url,
#         data=json.dumps(notification_martigny_data),
#         headers=json_header
#     )
#     assert res.status_code == 201

#     # Sion
#     login_user_via_session(client, librarian_sion_no_email.user)

#     res = client.post(
#         post_url,
#         data=json.dumps(notification_martigny_data),
#         headers=json_header
#     )
#     assert res.status_code == 403


# def test_notification_secure_api_update(client,
#                                         librarian_martigny_no_email,
#                                         librarian_sion_no_email,
#                                         notification_availabilty_martigny,
#                                         json_header):
#     """Test notification secure api update."""
#     login_user_via_session(client, librarian_martigny_no_email.user)
#     record_url = url_for('invenio_records_rest.notif_item',
#                          pid_value=notification_availabilty_martigny.pid)

#     data = notification_availabilty_martigny

#     # Sion
#     login_user_via_session(client, librarian_sion_no_email.user)

#     res = client.put(
#         record_url,
#         data=json.dumps(data),
#         headers=json_header
#     )
#     assert res.status_code == 403


# def test_notification_secure_api_delete(
#                                     client,
#                                     librarian_martigny_no_email,
#                                     librarian_sion_no_email,
#                                     notification_availabilty_martigny,
#                                     json_header):
#     """Test notification secure api delete."""
#     login_user_via_session(client, librarian_martigny_no_email.user)
#     record_url = url_for('invenio_records_rest.notif_item',
#                          pid_value=notification_availabilty_martigny.pid)
#     # Martigny
#     res = client.delete(record_url)
#     assert res.status_code == 204

#     # Sion
#     login_user_via_session(client, librarian_sion_no_email.user)

#     res = client.delete(record_url)
#     assert res.status_code == 410


def test_recall_notification(client, patron_martigny_no_email,
                             patron2_martigny_no_email,
                             item_lib_martigny, librarian_martigny_no_email,
                             circulation_policies, loc_public_martigny,
                             json_header):
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

    assert not loan.is_recalled()

    # test notification permissions
    res = client.post(
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
    assert res.status_code == 200

    flush_index(NotificationsSearch.Meta.index)

    assert loan.is_recalled()
