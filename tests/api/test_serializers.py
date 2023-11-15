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

"""Tests Serializers."""

import mock
from flask import url_for
from utils import VerifyRecordPermissionPatch, flush_index, get_json, \
    item_record_to_a_specific_loan_state, login_user

from rero_ils.modules.loans.models import LoanState
from rero_ils.modules.locations.api import LocationsSearch
from rero_ils.modules.operation_logs.api import OperationLogsSearch


def test_operation_logs_serializers(
    client,
    rero_json_header,
    patron_martigny,
    librarian_martigny,
    item_lib_martigny,
    loc_public_martigny,
    circulation_policies,
    lib_martigny_data
):
    """Test serializers for operation logs."""
    params = {
        'patron_pid': patron_martigny.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid,
        'pickup_location_pid': loc_public_martigny.pid,
    }
    item_record_to_a_specific_loan_state(
        item=item_lib_martigny, loan_state=LoanState.ITEM_AT_DESK,
        params=params, copy_item=True)
    # Force update ES index
    flush_index(OperationLogsSearch.Meta.index)
    list_url = url_for('invenio_records_rest.oplg_list')
    login_user(client, patron_martigny)
    response = client.get(list_url, headers=rero_json_header)
    assert response.status_code == 200
    data = get_json(response)
    loan = data.get('hits', {}).get('hits', [])[0].get('metadata', {})\
        .get('loan', {})
    libary_name = lib_martigny_data['name']
    # Check if the library data injected into the section
    assert libary_name == loan.get('transaction_location', {})\
        .get('library').get('name')
    assert libary_name == loan.get('pickup_location', {})\
        .get('library').get('name')


def test_patrons_serializers(
    client,
    json_header,
    librarian_martigny,
    librarian2_martigny,
    rero_json_header
):
    """Test serializers for patrons."""
    login_user(client, librarian_martigny)

    list_url = url_for('invenio_records_rest.ptrn_list')
    response = client.get(list_url, headers=json_header)
    assert response.status_code == 200

    # Get the first result and check if it contains all desired keys.
    data = get_json(response)
    hit = data['hits']['hits'][0]
    for key in ['created', 'updated', 'id', 'links', 'metadata']:
        assert key in hit
        assert hit[key]

    response = client.get(list_url, headers=rero_json_header)
    assert response.status_code == 200
    data = get_json(response)
    ptty_aggr = data.get('aggregations', {}).get('patron_type', {})
    assert all('name' in term for term in ptty_aggr.get('buckets', []))


def test_document_and_holdings_serializers(
    client,
    rero_json_header,
    document,
    librarian_martigny,
    lib_martigny,
    holding_lib_martigny
):
    """Test serializers for holdings."""
    login_user(client, librarian_martigny)

    doc_url = url_for('invenio_records_rest.doc_list')
    response = client.get(doc_url, headers=rero_json_header)
    assert response.status_code == 200
    doc_url = url_for('invenio_records_rest.doc_item', pid_value=document.pid)
    response = client.get(doc_url, headers=rero_json_header)
    assert response.status_code == 200

    holding_url = url_for('invenio_records_rest.hold_list')
    response = client.get(holding_url, headers=rero_json_header)
    assert response.status_code == 200
    data = get_json(response)
    record = data['hits']['hits'][0]['metadata']
    assert record.get('location', {}).get('name')
    assert record.get('library', {}).get('name')
    assert record.get('circulation_category', {}).get('name')


def test_loans_serializers(
    client,
    rero_json_header,
    patron_martigny,
    loc_public_martigny,
    loc_public_fully,
    librarian_martigny,
    item_lib_martigny,
    item_lib_fully,
    circulation_policies
):
    """Test serializers for loans."""
    # create somes loans on same item with different state
    params = {
        'patron_pid': patron_martigny.pid,
        'transaction_location_pid': loc_public_martigny.pid,
        'transaction_user_pid': librarian_martigny.pid,
        'pickup_location_pid': loc_public_martigny.pid,
    }
    item_record_to_a_specific_loan_state(
        item=item_lib_martigny, loan_state=LoanState.PENDING,
        params=params, copy_item=True)
    item_record_to_a_specific_loan_state(
        item=item_lib_martigny, loan_state=LoanState.ITEM_AT_DESK,
        params=params, copy_item=True)
    item_record_to_a_specific_loan_state(
        item=item_lib_martigny, loan_state=LoanState.ITEM_ON_LOAN,
        params=params, copy_item=True)
    params = {
        'patron_pid': patron_martigny.pid,
        'transaction_location_pid': loc_public_fully.pid,
        'transaction_user_pid': librarian_martigny.pid,
        'pickup_location_pid': loc_public_fully.pid,
        'checkin_transaction_location_pid': loc_public_martigny.pid
    }
    item_record_to_a_specific_loan_state(
        item=item_lib_fully,
        loan_state=LoanState.ITEM_IN_TRANSIT_TO_HOUSE,
        params=params, copy_item=True)

    list_url = url_for('invenio_records_rest.loanid_list')
    login_user(client, patron_martigny)
    response = client.get(list_url, headers=rero_json_header)
    assert response.status_code == 200
    data = get_json(response)

    records = data.get('hits', {}).get('hits', [])
    for record in records:
        data = record.get('metadata', {})
        if data.get('state') == 'PENDING':
            assert data.get('pickup_name')
        elif data.get('state') == 'ITEM_AT_DESK':
            assert data.get('rank') == 0
        elif data.get('state') == 'ITEM_ON_LOAN':
            assert data.get('overdue') is False
        elif data.get('state') == 'ITEM_IN_TRANSIT_TO_HOUSE':
            assert data.get('pickup_library_name')
            assert data.get('transaction_library_name')


def test_patron_transaction_events_serializers(
    client,
    rero_json_header,
    librarian_saxon,
    patron_transaction_overdue_event_saxon
):
    """Test serializers for patron transaction events."""
    login_user(client, librarian_saxon)
    list_url = url_for('invenio_records_rest.ptre_list')
    response = client.get(list_url, headers=rero_json_header)
    assert response.status_code == 200
    data = get_json(response)
    record = data.get('hits', {}).get('hits', [])[0]
    assert record.get('metadata', {}).get('library', {}).get('name')


def test_ill_requests_serializers(
    client,
    rero_json_header,
    patron_martigny,
    ill_request_martigny
):
    """Test serializers for ills requests."""
    login_user(client, patron_martigny)
    list_url = url_for('invenio_records_rest.illr_list')
    response = client.get(list_url, headers=rero_json_header)
    assert response.status_code == 200
    data = get_json(response)
    record = data.get('hits', {}).get('hits', [])[0]
    assert record.get('metadata', {}).get('pickup_location', {}).get('name')


# ACQUISITIONS MODULES ========================================================
@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_budgets_serializers(
    client, rero_json_header, lib_martigny, budget_2020_martigny
):
    """Test serializers for budgets requests."""
    budget = budget_2020_martigny
    item_url = url_for('invenio_records_rest.budg_item', pid_value=budget.pid)
    response = client.get(item_url, headers=rero_json_header)
    assert response.status_code == 200
    data = get_json(response)
    for key in ['is_current_budget']:
        assert key in data['metadata']


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_acq_accounts_serializers(
    client, rero_json_header, lib_martigny, budget_2020_martigny,
    acq_account_fiction_martigny
):
    """Test serializers for acq_accounts requests."""
    account = acq_account_fiction_martigny
    item_url = url_for('invenio_records_rest.acac_item', pid_value=account.pid)
    response = client.get(item_url, headers=rero_json_header)
    assert response.status_code == 200
    data = get_json(response)
    for key in ['depth', 'distribution', 'is_active', 'encumbrance_amount',
                'expenditure_amount', 'remaining_balance',
                'is_current_budget']:
        assert key in data['metadata']


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_acq_orders_serializers(
    client,
    rero_json_header,
    acq_order_fiction_martigny,
    acq_account_fiction_martigny,
    acq_order_line_fiction_martigny,
    lib_martigny
):
    """Test serializers for acq_orders/acq_order_lines requests."""
    order = acq_order_fiction_martigny
    item_url = url_for('invenio_records_rest.acor_item', pid_value=order.pid)
    response = client.get(item_url, headers=rero_json_header)
    assert response.status_code == 200
    data = get_json(response)
    for attr in ['is_current_budget']:
        assert attr in data['metadata']

    url = url_for(
        'invenio_records_rest.acol_list',
        q=f'acq_order.pid:{order.pid}'
    )
    response = client.get(url)
    assert response.status_code == 200
    data = get_json(response)
    acol_pid = data['hits']['hits'][0]['metadata']['pid']
    item_url = url_for('invenio_records_rest.acol_item', pid_value=acol_pid)
    response = client.get(item_url, headers=rero_json_header)
    assert response.status_code == 200
    data = get_json(response)
    for attr in ['is_current_budget']:
        assert attr in data['metadata']


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_acq_receipts_serializers(
    client,
    rero_json_header,
    acq_order_fiction_martigny,
    acq_account_fiction_martigny, acq_receipt_fiction_martigny,
    acq_receipt_line_1_fiction_martigny, acq_receipt_line_2_fiction_martigny,
    lib_martigny
):
    """Test serializers for acq_receipts/acq_receipt_lines requests."""
    acre = acq_receipt_fiction_martigny
    item_url = url_for('invenio_records_rest.acre_item', pid_value=acre.pid)
    response = client.get(item_url, headers=rero_json_header)
    assert response.status_code == 200
    data = get_json(response)
    for attr in ['currency', 'quantity', 'total_amount', 'receipt_lines',
                 'is_current_budget']:
        assert attr in data['metadata']

    list_url = url_for(
        'invenio_records_rest.acrl_list',
        q=f'acq_receipt.pid:{acre.pid}'
    )
    response = client.get(list_url, headers=rero_json_header)
    assert response.status_code == 200
    data = get_json(response)
    for hit in data['hits']['hits']:
        assert 'document' in hit['metadata']

    acrl_pid = data['hits']['hits'][0]['metadata']['pid']
    item_url = url_for('invenio_records_rest.acrl_item', pid_value=acrl_pid)
    response = client.get(item_url, headers=rero_json_header)
    assert response.status_code == 200
    data = get_json(response)
    for attr in ['is_current_budget']:
        assert attr in data['metadata']

    acor = acq_order_fiction_martigny
    url = url_for('invenio_records_rest.acor_list', q=f'pid:{acor.pid}')
    response = client.get(url, headers=rero_json_header)
    assert response.status_code == 200
    data = get_json(response)
    receipt_data_aggr = data.get('aggregations', {}).get('receipt_date', {})
    assert len(receipt_data_aggr.get('buckets', []))
    assert receipt_data_aggr.get('config', {})


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_cached_serializers(client, rero_json_header, item_lib_martigny,
                            loc_public_martigny, loc_public_martigny_data):
    """Test cached serializers."""

    # Ensure than cache used in some serializer is reset each time we request
    # a new search result serialization.
    #
    # To check this effect, we will request a first serialization about items
    # (items search serializer inherit from ``CachedDataSerializerMixin``).
    # After this first call, we will update a cached resource (item location).
    # Last step is to request again the items search and check if the location
    # return is affected by changed.

    # STEP#1 : first items search serialization
    item = item_lib_martigny
    list_url = url_for('invenio_records_rest.item_list', q=item.pid)
    response = client.get(list_url, headers=rero_json_header)
    assert response.status_code == 200

    # STEP#2 : update item location name
    location = loc_public_martigny
    location['name'] = 'new location name'
    location = location.update(location, dbcommit=True, reindex=True)
    flush_index(LocationsSearch.Meta.index)
    assert LocationsSearch().get_record_by_pid(location.pid)['name'] == \
           location.get('name')

    # STEP#3 : second items search serialization
    response = client.get(list_url, headers=rero_json_header)
    assert response.status_code == 200
    data = get_json(response)
    hit_metadata = data['hits']['hits'][0]['metadata']
    assert hit_metadata['location']['name'] == location.get('name')

    # reset location to initial values
    location.update(loc_public_martigny_data, dbcommit=True, reindex=True)
