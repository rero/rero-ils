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

"""Tests REST API patron payments."""

from copy import deepcopy

import mock
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import VerifyRecordPermissionPatch, get_json, postdata

from rero_ils.modules.loans.api import Loan
from rero_ils.modules.patron_transaction_events.models import \
    PatronTransactionEventType
from rero_ils.modules.patron_transactions.api import PatronTransaction
from rero_ils.modules.utils import get_ref_for_pid


def test_patron_payment(
        client, librarian_martigny,
        patron_transaction_overdue_event_martigny):
    """Test patron payment."""
    ptre = patron_transaction_overdue_event_martigny
    transaction = ptre.patron_transaction
    calculated_amount = sum(event.amount for event in transaction.events)
    transaction = PatronTransaction.get_record_by_pid(transaction.pid)
    assert calculated_amount == transaction.total_amount == 2.00

    login_user_via_session(client, librarian_martigny.user)
    post_entrypoint = 'invenio_records_rest.ptre_list'
    payment = deepcopy(ptre)

    # STEP#1 :: PARTIAL PAYMENT WITH TOO MUCH DECIMAL
    #   Try to pay a part of the transaction amount, but according to
    #   event amount restriction, only 2 decimals are allowed.
    del payment['pid']
    payment['type'] = PatronTransactionEventType.PAYMENT
    payment['subtype'] = 'cash'
    payment['amount'] = 0.545
    payment['operator'] = {
        '$ref': get_ref_for_pid('patrons', librarian_martigny.pid)
    }
    res, _ = postdata(client, post_entrypoint, payment)
    assert res.status_code == 400

    # STEP#2 :: PARTIAL PAYMENT WITH GOOD NUMBER OF DECIMALS
    #   Despite if a set a number with 3 decimals, if this number represent
    #   the value of a 2 decimals, it's allowed
    payment['amount'] = 0.540
    res, _ = postdata(client, post_entrypoint, payment)
    assert res.status_code == 201
    transaction = PatronTransaction.get_record_by_pid(transaction.pid)
    assert transaction.total_amount == 1.46
    assert transaction.status == 'open'

    # STEP#3 :: PAY TOO MUCH MONEY
    #   Try to proceed a payment with too much money, the system must
    #   reject the payment
    payment['amount'] = 2
    res, data = postdata(client, post_entrypoint, payment)
    assert res.status_code == 400

    # STEP34 :: ADD A DISPUTE
    #   Just to test if a ptte without amount doesn't break the process.
    dispute = deepcopy(ptre)
    del dispute['pid']
    del dispute['subtype']
    del dispute['amount']
    dispute['type'] = PatronTransactionEventType.DISPUTE
    dispute['note'] = 'this is a dispute note'
    dispute['operator'] = {
        '$ref': get_ref_for_pid('patrons', librarian_martigny.pid)
    }
    res, data = postdata(client, post_entrypoint, dispute)
    assert res.status_code == 201
    transaction = PatronTransaction.get_record_by_pid(transaction.pid)
    assert transaction.total_amount == 1.46
    assert transaction.status == 'open'

    # STEP#5 :: PAY THE REST
    #   Conclude the transaction by creation of a payment for the rest of the
    #   transaction
    payment['amount'] = transaction.total_amount
    res, _ = postdata(client, post_entrypoint, payment)
    assert res.status_code == 201
    transaction = PatronTransaction.get_record_by_pid(transaction.pid)
    assert transaction.total_amount == 0
    assert transaction.status == 'closed'


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_patron_transaction_events_facets(
    client, patron_transaction_overdue_event_martigny, loc_public_martigny,
    item4_lib_martigny, rero_json_header
):
    """Test record retrieval."""

    def _find_bucket(buckets, bucket_key):
        for bucket in buckets['buckets']:
            if bucket['key'] == bucket_key:
                return bucket

    # STEP#1 :: CHECK FACETS ARE PRESENT INTO SEARCH RESULT
    url = url_for('invenio_records_rest.ptre_list')
    res = client.get(url, headers=rero_json_header)
    data = get_json(res)
    facet_keys = [
        'category', 'owning_library', 'patron_type', 'total',
        'transaction_date', 'transaction_library', 'type'
    ]
    assert all(key in data['aggregations'] for key in facet_keys)

    owning_library = data['aggregations']['owning_library']['buckets']
    assert owning_library[0]['owning_location']['buckets'][0]['name'] == \
        loc_public_martigny['name']
    params = {'facets': ''}
    url = url_for('invenio_records_rest.ptre_list', **params)
    res = client.get(url, headers=rero_json_header)
    data = get_json(res)
    assert not data['aggregations']

    params = {'facets': 'type'}
    url = url_for('invenio_records_rest.ptre_list', **params)
    res = client.get(url, headers=rero_json_header)
    data = get_json(res)
    assert list(data['aggregations'].keys()) == ['type']

    # CHECK NESTED FACETS :: TYPE & SUBTYPE + OR SEARCH
    #    This test must be executed after `test_patron_payment` to retrieve
    #    some payments.
    params = {'facets': 'total'}
    url = url_for('invenio_records_rest.ptre_list', **params)
    res = client.get(url, headers=rero_json_header)
    data = get_json(res)

    total_bucket = data['aggregations']['total']
    assert total_bucket['doc_count'] == 2
    cash_subtype_aggr = _find_bucket(total_bucket['subtype'], 'cash')
    assert cash_subtype_aggr['doc_count'] == 2
    assert cash_subtype_aggr['subtotal']['value'] == 2.0

    #  filter with dummy subtypes :: no payment must be found
    params = {
        'facets': 'total',
        'type': PatronTransactionEventType.PAYMENT,
        'subtype': ['foo', 'bar']
    }
    url = url_for('invenio_records_rest.ptre_list', **params)
    res = client.get(url, headers=rero_json_header)
    data = get_json(res)
    total_bucket = data['aggregations']['total']
    assert total_bucket['doc_count'] == 0
    assert not _find_bucket(total_bucket['subtype'], 'cash')

    #  filter with an available subtype (cash) and an absent subtype
    #  (credit_card) :: payments must be found but only 'cash' subtype must
    #  exist
    params = {
        'facets': 'total',
        'type': PatronTransactionEventType.PAYMENT,
        'subtype': ['cash', 'credit_card']
    }
    url = url_for('invenio_records_rest.ptre_list', **params)
    res = client.get(url, headers=rero_json_header)
    data = get_json(res)
    total_bucket = data['aggregations']['total']
    assert total_bucket['doc_count'] == 2
    assert _find_bucket(total_bucket['subtype'], 'cash')
    assert not _find_bucket(total_bucket['subtype'], 'credit_card')

    # delete Location
    item4_links = item4_lib_martigny.get_links_to_me(get_pids=True)
    loan = Loan.get_record_by_pid(item4_links['loans'][0])
    loan.delete(dbcommit=True, delindex=True)
    item4_lib_martigny.delete(dbcommit=True, delindex=True)
    loc_pid = loc_public_martigny.pid
    loc_public_martigny.delete(dbcommit=True, delindex=True)
    url = url_for('invenio_records_rest.ptre_list')
    res = client.get(url, headers=rero_json_header)
    data = get_json(res)
    owning_library = data['aggregations']['owning_library']['buckets']
    assert owning_library[0]['owning_location']['buckets'][0]['name'] == \
        f'Unknown ({loc_pid})'
