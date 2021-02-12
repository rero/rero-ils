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
from datetime import datetime

import mock
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import VerifyRecordPermissionPatch, get_json, postdata, \
    to_relative_url

from rero_ils.modules.patron_transactions.api import PatronTransaction
from rero_ils.modules.utils import add_years


def test_patron_transactions_user_pid(patron_transaction_overdue_martigny):
    """Test patron_transactions.notification_user_pid property"""
    ptre = patron_transaction_overdue_martigny
    assert ptre.notification_transaction_user_pid == 'ptrn2'


def test_patron_transactions_permissions(
        client, patron_transaction_overdue_martigny, json_header):
    """Test record retrieval."""
    pid = patron_transaction_overdue_martigny.pid
    item_url = url_for('invenio_records_rest.pttr_item', pid_value=pid)

    res = client.get(item_url)
    assert res.status_code == 401

    res, _ = postdata(
        client,
        'invenio_records_rest.pttr_list',
        {}
    )
    assert res.status_code == 401

    client.put(
        item_url,
        data={},
        headers=json_header
    )
    res = client.delete(item_url)
    assert res.status_code == 401


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_patron_transactions_get(client, patron_transaction_overdue_martigny):
    """Test record retrieval."""
    transaction = patron_transaction_overdue_martigny
    pid = transaction.pid
    item_url = url_for('invenio_records_rest.pttr_item', pid_value=pid)
    list_url = url_for(
        'invenio_records_rest.pttr_list', q='pid:' + pid)
    item_url_with_resolve = url_for(
        'invenio_records_rest.pttr_item',
        pid_value=pid,
        resolve=1,
        sources=1
    )

    res = client.get(item_url)
    assert res.status_code == 200

    assert res.headers['ETag'] == '"{}"'.format(transaction.revision_id)

    data = get_json(res)
    assert transaction.dumps() == data['metadata']

    # Check metadata
    for k in ['created', 'updated', 'metadata', 'links']:
        assert k in data

    # Check self links
    res = client.get(to_relative_url(data['links']['self']))
    assert res.status_code == 200
    assert data == get_json(res)
    assert transaction.dumps() == data['metadata']

    # check resolve
    res = client.get(item_url_with_resolve)
    assert res.status_code == 200
    data = get_json(res)
    assert transaction.replace_refs().dumps() == data['metadata']

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    result = data['hits']['hits'][0]['metadata']
    del(result['document'])
    assert result == transaction.replace_refs()


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_patron_transactions_post_put_delete(
        client, lib_martigny, patron_transaction_overdue_martigny,
        json_header):
    """Test record retrieval."""
    item_url = url_for('invenio_records_rest.pttr_item', pid_value='new_pttr')
    list_url = url_for('invenio_records_rest.pttr_list', q='pid:new_pttr')
    transaction_data = deepcopy(patron_transaction_overdue_martigny)
    # Create record / POST
    transaction_data['pid'] = 'new_pttr'
    res, data = postdata(
        client,
        'invenio_records_rest.pttr_list',
        transaction_data
    )
    assert res.status_code == 201

    # Check that the returned record matches the given data
    assert data['metadata'] == transaction_data

    res = client.get(item_url)
    assert res.status_code == 200
    data = get_json(res)
    assert transaction_data == data['metadata']

    # Update record/PUT
    data = transaction_data
    data['note'] = 'Test Note'
    res = client.put(
        item_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 200
    assert res.headers['ETag'] != '"{}"'.format(transaction_data.revision_id)

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


def test_patron_transaction_shortcuts_utils(
        client, patron_transaction_overdue_martigny, loan_overdue_martigny):
    """Test patron transaction shortcuts and utils."""
    links = patron_transaction_overdue_martigny.get_links_to_me()
    assert 'events' in links

    assert not patron_transaction_overdue_martigny.can_delete

    reasons = patron_transaction_overdue_martigny.reasons_not_to_delete()
    assert 'links' in reasons

    assert patron_transaction_overdue_martigny.loan_pid == \
        loan_overdue_martigny.pid

    assert patron_transaction_overdue_martigny.patron_pid == \
        loan_overdue_martigny.patron_pid


def test_filtered_patron_transactions_get(
        client, librarian_martigny_no_email,
        patron_transaction_overdue_martigny,
        librarian_sion_no_email, patron_martigny_no_email
):
    """Test patron transaction filter by organisation."""
    list_url = url_for('invenio_records_rest.pttr_list')

    res = client.get(list_url)
    assert res.status_code == 401

    login_user_via_session(client, patron_martigny_no_email.user)

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total']['value'] == 1

    # Martigny
    login_user_via_session(client, librarian_martigny_no_email.user)

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total']['value'] == 1

    # Sion
    login_user_via_session(client, librarian_sion_no_email.user)
    list_url = url_for('invenio_records_rest.pttr_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total']['value'] == 0


def test_patron_transaction_secure_api(
        client, json_header, patron_transaction_overdue_martigny,
        librarian_martigny_no_email, librarian_sion_no_email,
        system_librarian_martigny_no_email, system_librarian_sion_no_email,
        patron_transaction_overdue_saxon, patron_martigny_no_email):
    """Test patron transaction secure api access."""
    login_user_via_session(client, patron_martigny_no_email.user)
    record_url = url_for('invenio_records_rest.pttr_item',
                         pid_value=patron_transaction_overdue_martigny.pid)

    res = client.get(record_url)
    # a librarian is authorized to access any patron transaction of its library
    assert res.status_code == 200

    # Martigny
    login_user_via_session(client, librarian_martigny_no_email.user)
    record_url = url_for('invenio_records_rest.pttr_item',
                         pid_value=patron_transaction_overdue_martigny.pid)

    res = client.get(record_url)
    # a librarian is authorized to access any patron transaction of its library
    assert res.status_code == 200

    record_url = url_for('invenio_records_rest.pttr_item',
                         pid_value=patron_transaction_overdue_saxon.pid)

    res = client.get(record_url)
    # a librarian can access any patron transaction of its organisation
    assert res.status_code == 200

    login_user_via_session(client, system_librarian_martigny_no_email.user)
    res = client.get(record_url)
    # a sys_librarian can access any patron transaction of its organisation
    assert res.status_code == 200

    # Sion
    login_user_via_session(client, librarian_sion_no_email.user)
    record_url = url_for('invenio_records_rest.pttr_item',
                         pid_value=patron_transaction_overdue_martigny.pid)

    res = client.get(record_url)
    # librarian can not access any patron transaction of other organisation
    assert res.status_code == 403

    login_user_via_session(client, system_librarian_sion_no_email.user)
    res = client.get(record_url)
    # a sys_librarian can not access any patron transaction of other org
    assert res.status_code == 403


def test_patron_transaction_secure_api_create(
        client, librarian_martigny_no_email,
        librarian_sion_no_email, patron_transaction_overdue_martigny,
        system_librarian_martigny_no_email,
        system_librarian_sion_no_email):
    """Test patron transction secure api create."""
    # Martigny
    login_user_via_session(client, librarian_martigny_no_email.user)
    post_entrypoint = 'invenio_records_rest.pttr_list'
    patron_transaction = deepcopy(patron_transaction_overdue_martigny)
    del patron_transaction['pid']
    res, _ = postdata(
        client,
        post_entrypoint,
        patron_transaction
    )
    # librarian is authorized to create a patron transaction in its library.
    assert res.status_code == 201

    patron_transaction_2 = deepcopy(patron_transaction_overdue_martigny)

    del patron_transaction_2['pid']
    res, _ = postdata(
        client,
        post_entrypoint,
        patron_transaction_2
    )
    # librarian is can create a patron transaction in other libraries.
    assert res.status_code == 201

    login_user_via_session(client, system_librarian_martigny_no_email.user)
    res, _ = postdata(
        client,
        post_entrypoint,
        patron_transaction_2
    )
    # sys_librarian is authorized to create any patron transaction in its org.
    assert res.status_code == 201

    # Sion
    login_user_via_session(client, librarian_sion_no_email.user)

    patron_transaction_3 = deepcopy(patron_transaction_overdue_martigny)
    del patron_transaction_3['pid']

    res, _ = postdata(
        client,
        post_entrypoint,
        patron_transaction_3
    )
    # librarian is not authorized to create a patron transaction at other org.
    assert res.status_code == 403

    login_user_via_session(client, system_librarian_sion_no_email.user)
    res, _ = postdata(
        client,
        post_entrypoint,
        patron_transaction_3
    )
    # sys_librarian can not to create a patron transaction in other org.
    assert res.status_code == 403


def test_patron_transaction_secure_api_update(
        client, patron_transaction_overdue_saxon,
        patron_transaction_overdue_martigny, librarian_martigny_no_email,
        librarian_sion_no_email, json_header,
        system_librarian_martigny_no_email, system_librarian_sion_no_email):
    """Test patron transaction secure api update."""
    # Martigny
    login_user_via_session(client, librarian_martigny_no_email.user)
    record_url = url_for('invenio_records_rest.pttr_item',
                         pid_value=patron_transaction_overdue_martigny.pid)

    patron_transaction_overdue_martigny['note'] = 'New Note'
    res = client.put(
        record_url,
        data=json.dumps(patron_transaction_overdue_martigny),
        headers=json_header
    )
    # librarian is authorized to update a patron transaction in its library.
    assert res.status_code == 200

    record_url = url_for('invenio_records_rest.pttr_item',
                         pid_value=patron_transaction_overdue_saxon.pid)

    patron_transaction_overdue_saxon['note'] = 'New Note'
    res = client.put(
        record_url,
        data=json.dumps(patron_transaction_overdue_saxon),
        headers=json_header
    )
    # librarian is can update a patron transaction of another library.
    assert res.status_code == 200

    login_user_via_session(client, system_librarian_martigny_no_email.user)
    res = client.put(
        record_url,
        data=json.dumps(patron_transaction_overdue_saxon),
        headers=json_header
    )
    # sys_librarian is authorized to update any patron transaction of its org.
    assert res.status_code == 200

#     # Sion
    login_user_via_session(client, librarian_sion_no_email.user)

    res = client.put(
        record_url,
        data=json.dumps(patron_transaction_overdue_saxon),
        headers=json_header
    )
    # librarian can not update any patron transaction of another org.
    assert res.status_code == 403

    login_user_via_session(client, system_librarian_sion_no_email.user)
    res = client.put(
        record_url,
        data=json.dumps(patron_transaction_overdue_saxon),
        headers=json_header
    )
    assert res.status_code == 403


def test_patron_transaction_secure_api_delete(
        client, patron_transaction_overdue_saxon,
        patron_transaction_overdue_martigny, librarian_martigny_no_email,
        librarian_sion_no_email, system_librarian_martigny_no_email,
        system_librarian_sion_no_email):
    """Test patron transaction secure api delete."""
    # Sion
    login_user_via_session(client, librarian_sion_no_email.user)

    record_url = url_for('invenio_records_rest.pttr_item',
                         pid_value=patron_transaction_overdue_martigny.pid)
    res = client.delete(record_url)
    # librarian can not delete any patron transaction of other org.
    assert res.status_code == 403

    login_user_via_session(client, system_librarian_sion_no_email.user)
    res = client.delete(record_url)
    # sys_ibrarian can not delete any patron transaction of other org.
    assert res.status_code == 403

    login_user_via_session(client, librarian_martigny_no_email.user)
    record_url = url_for('invenio_records_rest.pttr_item',
                         pid_value=patron_transaction_overdue_saxon.pid)

    # delete the events of the patron_transation
    for patron_event in patron_transaction_overdue_saxon.events:
        patron_event.delete(dbcommit=True, delindex=True)

    res = client.delete(record_url)
    # librarian is authorized to delete any patron transaction of its library.
    assert res.status_code == 204

    record_url = url_for('invenio_records_rest.pttr_item',
                         pid_value=patron_transaction_overdue_martigny.pid)

    # delete the events of the patron_transation
    for patron_event in patron_transaction_overdue_martigny.events:
        patron_event.delete(dbcommit=True, delindex=True)

    res = client.delete(record_url)
    # librarian can delete any patron transaction of other libraries.
    assert res.status_code == 204


def test_patron_subscription_transaction(
        patron_type_youngsters_sion, patron_sion_no_email):
    """Test the creation of a subscription transaction for a patron."""
    subscription_start_date = datetime.now()
    subscription_end_date = add_years(subscription_start_date, 1)
    assert subscription_end_date.year == subscription_start_date.year + 1
    assert subscription_end_date.month == subscription_start_date.month
    assert subscription_end_date.day == subscription_start_date.day

    subscription = PatronTransaction.create_subscription_for_patron(
        patron_sion_no_email,
        patron_type_youngsters_sion,
        subscription_start_date,
        subscription_end_date,
        dbcommit=True,
        reindex=True,
        delete_pid=True
    )
    assert subscription.get_number_of_patron_transaction_events() == 1
    event = list(subscription.events)[0]
    assert event.get('type') == 'fee'
    assert event.get('subtype') == 'other'
    assert event.get('amount') == subscription.get('total_amount')


def test_get_transactions_pids_for_patron(patron_sion_no_email):
    """Test function get_transactions_pids_for_patron."""
    assert PatronTransaction.get_transactions_count_for_patron(
        patron_sion_no_email.pid
    ) == 2
    assert len(list(PatronTransaction.get_transactions_pids_for_patron(
        patron_sion_no_email.pid, status='open'
    ))) == 2
    assert len(list(PatronTransaction.get_transactions_pids_for_patron(
        patron_sion_no_email.pid, status='closed'
    ))) == 0
