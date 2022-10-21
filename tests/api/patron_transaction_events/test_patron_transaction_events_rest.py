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

"""Tests REST API patron transactions."""

import json
from copy import deepcopy

import mock
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import VerifyRecordPermissionPatch, get_json, postdata, \
    to_relative_url

from rero_ils.modules.patron_transaction_events.api import \
    PatronTransactionEvent


def test_patron_transaction_events_permissions(
        client, patron_transaction_overdue_event_martigny, json_header):
    """Test record retrieval."""
    pid = patron_transaction_overdue_event_martigny.pid
    item_url = url_for('invenio_records_rest.ptre_item', pid_value=pid)

    res = client.get(item_url)
    assert res.status_code == 401

    res, _ = postdata(
        client,
        'invenio_records_rest.ptre_list',
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


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_patron_transaction_events_get(
        client, patron_transaction_overdue_event_martigny):
    """Test record retrieval."""
    patron_event = patron_transaction_overdue_event_martigny
    pid = patron_event.pid
    item_url = url_for('invenio_records_rest.ptre_item', pid_value=pid)
    list_url = url_for('invenio_records_rest.ptre_list', q=f'pid:{pid}')
    item_url_with_resolve = url_for(
        'invenio_records_rest.ptre_item',
        pid_value=pid,
        resolve=1,
        sources=1
    )

    res = client.get(item_url)
    assert res.status_code == 200

    assert res.headers['ETag'] == f'"{patron_event.revision_id}"'

    data = get_json(res)
    assert patron_event.dumps() == data['metadata']

    # Check metadata
    for k in ['created', 'updated', 'metadata', 'links']:
        assert k in data

    # Check self links
    res = client.get(to_relative_url(data['links']['self']))
    assert res.status_code == 200
    assert data == get_json(res)
    assert patron_event.dumps() == data['metadata']

    # check resolve
    res = client.get(item_url_with_resolve)
    assert res.status_code == 200
    data = get_json(res)
    assert patron_event.replace_refs().dumps() == data['metadata']

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    result = data['hits']['hits'][0]['metadata']
    # delete dynamically added keys (listener)
    del result['organisation']
    del result['patron']
    del result['category']
    del result['owning_library']
    del result['owning_location']
    del result['patron_type']

    assert result == patron_event.replace_refs()


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_patron_transaction_events_post_put_delete(
        client, patron_transaction_overdue_event_martigny,
        json_header):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.ptre_item', pid_value='new_ptre')
    list_url = url_for('invenio_records_rest.ptre_list', q='pid:new_ptre')
    event_data = deepcopy(patron_transaction_overdue_event_martigny)
    # Create record / POST
    event_data['pid'] = 'new_ptre'
    res, data = postdata(
        client,
        'invenio_records_rest.ptre_list',
        event_data
    )
    assert res.status_code == 201

    # Check that the returned record matches the given data
    assert data['metadata'] == event_data

    res = client.get(item_url)
    assert res.status_code == 200
    data = get_json(res)
    assert event_data == data['metadata']

    # Update record/PUT
    data = event_data
    data['note'] = 'Test Note'
    res = client.put(
        item_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 200
    assert res.headers['ETag'] != f'"{event_data.revision_id}"'

    # Check that the returned record matches the given data
    data = get_json(res)
    assert data['metadata']['note'] == 'Test Note'

    res = client.get(item_url)
    assert res.status_code == 200

    data = get_json(res)
    assert data['metadata']['note'] == 'Test Note'

    res = client.get(list_url)
    assert res.status_code == 200

    data = get_json(res)['hits']['hits'][0]
    assert data['metadata']['note'] == 'Test Note'

    # Delete record/DELETE
    res = client.delete(item_url)
    assert res.status_code == 204

    res = client.get(item_url)
    assert res.status_code == 410


def test_patron_transaction_event_utils_shortcuts(
        client, patron_transaction_overdue_event_martigny,
        loan_overdue_martigny):
    """Test patron transaction utils and shortcuts."""
    can, reasons = patron_transaction_overdue_event_martigny.can_delete
    assert can
    assert reasons == {}

    assert patron_transaction_overdue_event_martigny.patron_pid == \
        loan_overdue_martigny.patron_pid


def test_filtered_patron_transaction_events_get(
        client, librarian_martigny,
        patron_transaction_overdue_event_martigny,
        librarian_sion, patron_martigny
):
    """Test patron transaction event filter by organisation."""
    list_url = url_for('invenio_records_rest.ptre_list')

    login_user_via_session(client, patron_martigny.user)
    res = client.get(list_url)
    assert res.status_code == 200

    # Martigny
    login_user_via_session(client, librarian_martigny.user)

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total']['value'] == 1

    # Sion
    login_user_via_session(client, librarian_sion.user)
    list_url = url_for('invenio_records_rest.ptre_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total']['value'] == 0


def test_patron_transaction_event_secure_api(
        client, json_header, patron_transaction_overdue_event_martigny,
        librarian_martigny, librarian_sion,
        system_librarian_martigny, system_librarian_sion,
        patron_transaction_overdue_event_saxon, patron_martigny):
    """Test patron transaction event secure api access."""
    # test if a 'creation_date' attribute is created if not present into data
    trans_data = deepcopy(patron_transaction_overdue_event_martigny)
    del trans_data['creation_date']
    trans = PatronTransactionEvent.create(trans_data, delete_pid=True)
    assert trans.get('creation_date')

    record_url = url_for(
        'invenio_records_rest.ptre_item',
        pid_value=patron_transaction_overdue_event_martigny.pid)

    login_user_via_session(client, patron_martigny.user)
    res = client.get(record_url)
    # a patron is authorized to access his events
    assert res.status_code == 200

    # Martigny
    login_user_via_session(client, librarian_martigny.user)

    res = client.get(record_url)
    # a librarian is authorized to access any patron event of its library
    assert res.status_code == 200

    record_url = url_for('invenio_records_rest.ptre_item',
                         pid_value=patron_transaction_overdue_event_saxon.pid)

    res = client.get(record_url)
    # a librarian can access any patron event of its organisation
    assert res.status_code == 200

    login_user_via_session(client, system_librarian_martigny.user)
    res = client.get(record_url)
    # a sys_librarian can access any patron event of its organisation
    assert res.status_code == 200

    # Sion
    login_user_via_session(client, librarian_sion.user)
    record_url = url_for(
        'invenio_records_rest.ptre_item',
        pid_value=patron_transaction_overdue_event_martigny.pid)

    res = client.get(record_url)
    # librarian can not access any patron event of other organisation
    assert res.status_code == 403

    login_user_via_session(client, system_librarian_sion.user)
    res = client.get(record_url)
    # a sys_librarian can not access any patron event of other org
    assert res.status_code == 403


def test_patron_transaction_event_secure_api_create(
        client, librarian_martigny,
        librarian_sion, patron_transaction_overdue_event_martigny,
        system_librarian_martigny,
        system_librarian_sion):
    """Test patron transaction event secure api create."""
    # Martigny
    login_user_via_session(client, librarian_martigny.user)
    post_entrypoint = 'invenio_records_rest.ptre_list'
    patron_event = deepcopy(patron_transaction_overdue_event_martigny)
    del patron_event['pid']
    res, _ = postdata(
        client,
        post_entrypoint,
        patron_event
    )
    # librarian is authorized to create a patron event in its library.
    assert res.status_code == 201

    patron_event_2 = deepcopy(patron_transaction_overdue_event_martigny)

    del patron_event_2['pid']
    res, _ = postdata(
        client,
        post_entrypoint,
        patron_event_2
    )
    # librarian is can create a patron event in other libraries.
    assert res.status_code == 201

    login_user_via_session(client, system_librarian_martigny.user)
    res, _ = postdata(
        client,
        post_entrypoint,
        patron_event_2
    )
    # sys_librarian is authorized to create any patron event in its org.
    assert res.status_code == 201

    # Sion
    login_user_via_session(client, librarian_sion.user)

    patron_event_3 = deepcopy(patron_transaction_overdue_event_martigny)
    del patron_event_3['pid']

    res, _ = postdata(
        client,
        post_entrypoint,
        patron_event_3
    )
    # librarian is not authorized to create a patron event at other org.
    assert res.status_code == 403

    login_user_via_session(client, system_librarian_sion.user)
    res, _ = postdata(
        client,
        post_entrypoint,
        patron_event_3
    )
    # sys_librarian can not to create a patron event in other org.
    assert res.status_code == 403


def test_patron_transaction_event_secure_api_update(
        client, patron_transaction_overdue_event_saxon,
        patron_transaction_overdue_event_martigny, librarian_martigny,
        librarian_sion, json_header,
        system_librarian_martigny, system_librarian_sion):
    """Test patron transaction event secure api update."""
    # Martigny
    login_user_via_session(client, librarian_martigny.user)
    record_url = url_for(
        'invenio_records_rest.ptre_item',
        pid_value=patron_transaction_overdue_event_martigny.pid)

    patron_transaction_overdue_event_martigny['note'] = 'New Note'
    res = client.put(
        record_url,
        data=json.dumps(patron_transaction_overdue_event_martigny),
        headers=json_header
    )
    # librarian is authorized to update a patron event in its library.
    assert res.status_code == 200

    record_url = url_for('invenio_records_rest.ptre_item',
                         pid_value=patron_transaction_overdue_event_saxon.pid)

    patron_transaction_overdue_event_saxon['note'] = 'New Note'
    res = client.put(
        record_url,
        data=json.dumps(patron_transaction_overdue_event_saxon),
        headers=json_header
    )
    # librarian is can update a patron event of another library.
    assert res.status_code == 200

    login_user_via_session(client, system_librarian_martigny.user)
    res = client.put(
        record_url,
        data=json.dumps(patron_transaction_overdue_event_saxon),
        headers=json_header
    )
    # sys_librarian is authorized to update any patron event of its org.
    assert res.status_code == 200

#     # Sion
    login_user_via_session(client, librarian_sion.user)

    res = client.put(
        record_url,
        data=json.dumps(patron_transaction_overdue_event_saxon),
        headers=json_header
    )
    # librarian can not update any patron event of another org.
    assert res.status_code == 403

    login_user_via_session(client, system_librarian_sion.user)
    res = client.put(
        record_url,
        data=json.dumps(patron_transaction_overdue_event_saxon),
        headers=json_header
    )
    assert res.status_code == 403


def test_patron_transaction_event_secure_api_delete(
        client, patron_transaction_overdue_event_saxon,
        patron_transaction_overdue_event_martigny, librarian_martigny,
        librarian_sion, system_librarian_martigny,
        system_librarian_sion):
    """Test patron transaction event secure api delete."""
    # Sion
    login_user_via_session(client, librarian_sion.user)

    record_url = url_for(
        'invenio_records_rest.ptre_item',
        pid_value=patron_transaction_overdue_event_martigny.pid)
    res = client.delete(record_url)
    # librarian can not delete any patron event of other org.
    assert res.status_code == 403

    login_user_via_session(client, system_librarian_sion.user)
    res = client.delete(record_url)
    # sys_ibrarian can not delete any patron event of other org.
    assert res.status_code == 403

    login_user_via_session(client, librarian_martigny.user)
    record_url = url_for('invenio_records_rest.ptre_item',
                         pid_value=patron_transaction_overdue_event_saxon.pid)

    res = client.delete(record_url)
    # librarian is authorized to delete any patron event of its library.
    assert res.status_code == 204

    record_url = url_for(
        'invenio_records_rest.ptre_item',
        pid_value=patron_transaction_overdue_event_martigny.pid)

    res = client.delete(record_url)
    # librarian can delete any patron event of other libraries.
    assert res.status_code == 204
