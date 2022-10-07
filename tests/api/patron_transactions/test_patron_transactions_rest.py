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

from rero_ils.modules.patron_transactions.utils import \
    create_subscription_for_patron, get_transactions_pids_for_patron
from rero_ils.modules.utils import add_years


def test_patron_transactions_user_pid(patron_transaction_overdue_martigny):
    """Test patron_transactions.notification_user_pid property"""
    ptre = patron_transaction_overdue_martigny
    assert ptre.notification_transaction_user_pid == 'ptrn2'


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_patron_transactions_get(client, patron_transaction_overdue_martigny):
    """Test record retrieval."""
    transaction = patron_transaction_overdue_martigny
    pid = transaction.pid
    item_url = url_for('invenio_records_rest.pttr_item', pid_value=pid)
    list_url = url_for('invenio_records_rest.pttr_list', q=f'pid:{pid}')
    item_url_with_resolve = url_for(
        'invenio_records_rest.pttr_item',
        pid_value=pid,
        resolve=1,
        sources=1
    )

    res = client.get(item_url)
    assert res.status_code == 200
    assert res.headers['ETag'] == f'"{transaction.revision_id}"'

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
    del result['document']
    del result['library']
    del result['item']
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
    assert res.headers['ETag'] != f'"{transaction_data.revision_id}"'

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


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_patron_transaction_photocopy_create(
    client, lib_martigny,
    patron_transaction_photocopy_martigny_data, system_librarian_martigny,
):
    """Test creation and delete of photocopy fee transaction."""
    # Create another kind of transaction
    transaction_data = deepcopy(patron_transaction_photocopy_martigny_data)
    del transaction_data['pid']
    res, data = postdata(
        client,
        'invenio_records_rest.pttr_list',
        transaction_data
    )
    assert res.status_code == 201
    pid = data['metadata']['pid']
    item_url = url_for('invenio_records_rest.pttr_item', pid_value=pid)
    res = client.delete(item_url)
    assert res.status_code == 204


def test_patron_transaction_shortcuts_utils(
        client, patron_transaction_overdue_martigny, loan_overdue_martigny):
    """Test patron transaction shortcuts and utils."""
    can, reasons = patron_transaction_overdue_martigny.can_delete
    assert not can
    assert reasons['links']['events']

    assert patron_transaction_overdue_martigny.loan_pid == \
        loan_overdue_martigny.pid

    assert patron_transaction_overdue_martigny.patron_pid == \
        loan_overdue_martigny.patron_pid


def test_filtered_patron_transactions_get(
        client, librarian_martigny,
        patron_transaction_overdue_martigny,
        librarian_sion, patron_martigny
):
    """Test patron transaction filter by organisation."""
    list_url = url_for('invenio_records_rest.pttr_list')

    res = client.get(list_url)
    assert res.status_code == 401

    login_user_via_session(client, patron_martigny.user)

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total']['value'] == 1

    # Martigny
    login_user_via_session(client, librarian_martigny.user)

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total']['value'] == 1

    # Sion
    login_user_via_session(client, librarian_sion.user)
    list_url = url_for('invenio_records_rest.pttr_list')

    res = client.get(list_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['hits']['total']['value'] == 0


def test_patron_subscription_transaction(
        patron_type_youngsters_sion, patron_sion):
    """Test the creation of a subscription transaction for a patron."""
    subscription_start_date = datetime.now()
    subscription_end_date = add_years(subscription_start_date, 1)
    assert subscription_end_date.year == subscription_start_date.year + 1
    assert subscription_end_date.month == subscription_start_date.month
    assert subscription_end_date.day == subscription_start_date.day

    subscription = create_subscription_for_patron(
        patron_sion,
        patron_type_youngsters_sion,
        subscription_start_date,
        subscription_end_date,
        dbcommit=True,
        reindex=True,
        delete_pid=True
    )
    assert subscription.get_links_to_me() == {'events': 1}
    assert subscription.get_links_to_me(get_pids=True)
    event = list(subscription.events)[0]
    assert event.get('type') == 'fee'
    assert event.get('subtype') == 'other'
    assert event.get('amount') == subscription.get('total_amount')


def test_get_transactions_pids_for_patron(patron_sion):
    """Test function get_transactions_pids_for_patron."""
    assert len(list(get_transactions_pids_for_patron(
        patron_sion.pid, status='open'
    ))) == 2
    assert not list(get_transactions_pids_for_patron(
        patron_sion.pid, status='closed'))
