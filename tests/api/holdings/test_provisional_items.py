# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
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


"""Test provisional items."""

from __future__ import absolute_import, print_function

from datetime import datetime, timezone

from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import get_json, postdata

from rero_ils.modules.items.api import Item
from rero_ils.modules.items.models import ItemStatus, TypeOfItem
from rero_ils.modules.items.tasks import delete_provisional_items
from rero_ils.modules.items.utils import \
    get_provisional_items_candidate_to_delete
from rero_ils.modules.loans.api import Loan
from rero_ils.modules.loans.models import LoanAction, LoanState
from rero_ils.modules.patron_transactions.api import PatronTransaction
from rero_ils.modules.utils import get_ref_for_pid


def test_provisional_items_creation(client, document, org_martigny,
                                    holding_lib_martigny_w_patterns,
                                    provisional_item_lib_martigny_data,
                                    json_header, item_lib_martigny,
                                    patron_martigny,
                                    system_librarian_martigny):
    """Test creation of provisional items."""
    holding = holding_lib_martigny_w_patterns
    provisional_item_lib_martigny_data['holding'] = \
        {'$ref': get_ref_for_pid('hold', holding.pid)}
    item = Item.create(
        provisional_item_lib_martigny_data, dbcommit=True, reindex=True)

    item_url = url_for('invenio_records_rest.item_item', pid_value=item.pid)
    res = client.get(item_url)
    assert res.status_code == 200
    item_es = Item(get_json(res).get('metadata'))
    assert item_es.get('type') == TypeOfItem.PROVISIONAL
    assert item_es.status == ItemStatus.ON_SHELF
    assert item_es.holding_pid == holding.pid

    # TEST: logged patrons can not have the provisional items in the results.
    # for both global and insitutional view.
    login_user_via_session(client, patron_martigny.user)

    list_url = url_for('invenio_records_rest.item_list', view='org1')
    response = client.get(list_url, headers=json_header)
    assert response.status_code == 200
    data = get_json(response)
    items = data['hits']['hits']
    assert len(items) == 1
    assert items[0]['metadata']['pid'] == item_lib_martigny.pid

    list_url = url_for('invenio_records_rest.item_list', view='global')
    response = client.get(list_url, headers=json_header)
    assert response.status_code == 200
    data = get_json(response)
    items = data['hits']['hits']
    assert len(items) == 1
    assert items[0]['metadata']['pid'] == item_lib_martigny.pid

    # TEST: logged librarians can have the provisional items in the results.
    # provisional items are still not available for the global and other views.
    login_user_via_session(client, system_librarian_martigny.user)

    list_url = url_for('invenio_records_rest.item_list')
    response = client.get(list_url, headers=json_header)
    assert response.status_code == 200
    data = get_json(response)
    items = data['hits']['hits']
    assert len(items) == 2

    list_url = url_for('invenio_records_rest.item_list', view='global')
    response = client.get(list_url, headers=json_header)
    assert response.status_code == 200
    data = get_json(response)
    items = data['hits']['hits']
    assert len(items) == 1
    assert items[0]['metadata']['pid'] == item_lib_martigny.pid

    list_url = url_for('invenio_records_rest.item_list', view='org1')
    response = client.get(list_url, headers=json_header)
    assert response.status_code == 200
    data = get_json(response)
    items = data['hits']['hits']
    assert len(items) == 1
    assert items[0]['metadata']['pid'] == item_lib_martigny.pid


def test_holding_requests(client, patron_martigny, loc_public_martigny,
                          circulation_policies, librarian_martigny,
                          holding_lib_martigny_w_patterns, lib_martigny,
                          item_lib_martigny, org_martigny):
    """Test holding patron request."""
    login_user_via_session(client, patron_martigny.user)
    holding = holding_lib_martigny_w_patterns
    description = 'Year: 2000 / volume: 15 / number: 22 / pages: 11-12'
    # test fails when there is a missing description or holding_pid
    res, data = postdata(
        client,
        'api_holding.patron_request',
        dict(
            holding_pid=holding.pid,
            pickup_location_pid=loc_public_martigny.pid
        )
    )
    assert res.status_code == 400
    res, data = postdata(
        client,
        'api_holding.patron_request',
        dict(
            description=description,
            pickup_location_pid=loc_public_martigny.pid
        )
    )
    assert res.status_code == 404
    # test passes when all required parameters are given
    res, data = postdata(
        client,
        'api_holding.patron_request',
        dict(
            holding_pid=holding.pid,
            pickup_location_pid=loc_public_martigny.pid,
            description=description
        )
    )
    assert res.status_code == 200
    loan = Loan.get_record_by_pid(
        data.get('action_applied')[LoanAction.REQUEST].get('pid'))
    assert loan.state == LoanState.PENDING
    item = Item.get_record_by_pid(loan.item_pid)
    assert item.get('type') == TypeOfItem.PROVISIONAL
    assert item.status == ItemStatus.ON_SHELF
    assert item.holding_pid == holding.pid
    assert item.get('enumerationAndChronology') == description
    # checkout the item to the requested patron
    login_user_via_session(client, librarian_martigny.user)
    res, data = postdata(client, 'api_item.checkout', dict(
        item_pid=item.pid,
        patron_pid=patron_martigny.pid,
        transaction_location_pid=loc_public_martigny.pid,
        transaction_user_pid=librarian_martigny.pid,
    ))
    assert res.status_code == 200
    loan_pid = data.get('action_applied')[LoanAction.CHECKOUT].get('pid')
    assert loan_pid == loan.pid
    item = Item.get_record_by_pid(item.pid)
    assert item.status == ItemStatus.ON_LOAN
    # return the item at the owning library
    res, data = postdata(
        client,
        'api_item.checkin',
        dict(
            item_pid=item.pid,
            transaction_location_pid=loc_public_martigny.pid,
            transaction_user_pid=librarian_martigny.pid
        )
    )
    assert res.status_code == 200
    item = Item.get_record_by_pid(item.pid)
    assert item.status == ItemStatus.ON_SHELF

    # test requests made by a librarian
    # test fails when there are missing parameters
    res, data = postdata(
        client,
        'api_holding.librarian_request',
        dict(
            holding_pid=holding.pid,
            pickup_location_pid=loc_public_martigny.pid,
            description=description,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny.pid
        )
    )
    assert res.status_code == 400
    res, data = postdata(
        client,
        'api_holding.librarian_request',
        dict(
            holding_pid=holding.pid,
            pickup_location_pid=loc_public_martigny.pid,
            description=description,
            patron_pid=patron_martigny.pid,
            transaction_library_pid=lib_martigny.pid
        )
    )
    assert res.status_code == 400
    res, data = postdata(
        client,
        'api_holding.librarian_request',
        dict(
            holding_pid=holding.pid,
            pickup_location_pid=loc_public_martigny.pid,
            patron_pid=patron_martigny.pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny.pid
        )
    )
    assert res.status_code == 400
    # test passes when all required parameters are given
    res, data = postdata(
        client,
        'api_holding.librarian_request',
        dict(
            holding_pid=holding.pid,
            pickup_location_pid=loc_public_martigny.pid,
            description=description,
            patron_pid=patron_martigny.pid,
            transaction_library_pid=lib_martigny.pid,
            transaction_user_pid=librarian_martigny.pid
        )
    )
    assert res.status_code == 200
    loan_2 = Loan.get_record_by_pid(
        data.get('action_applied')[LoanAction.REQUEST].get('pid'))
    assert loan_2.state == LoanState.PENDING
    item_2 = Item.get_record_by_pid(loan_2.item_pid)
    assert item_2.get('type') == TypeOfItem.PROVISIONAL
    assert item_2.status == ItemStatus.ON_SHELF
    assert item_2.holding_pid == holding.pid
    assert item_2.get('enumerationAndChronology') == description
    assert item_2.pid != item.pid

    all_item_pids = list(Item.get_all_pids())
    assert all_item_pids

    # test delete provisional items with no active fees/loans
    report = delete_provisional_items()
    assert report.get('number_of_deleted_items')
    assert report.get('number_of_candidate_items_to_delete')
    # assert that not deleted items are either having loans/fees or not
    # provisional items
    left_item_pids = list(Item.get_all_pids())
    assert left_item_pids
    for pid in left_item_pids:
        record = Item.get_record_by_pid(pid)
        can, _ = record.can_delete
        assert not can or record.get('type') != TypeOfItem.PROVISIONAL
    # item_2 has pending loans then it should not be removed
    assert item_2.pid in left_item_pids
    assert item_2 in get_provisional_items_candidate_to_delete()
    # add fee to item_2 and make sure it will not be candidate at the deletion.
    data = {
        'loan': {'$ref': get_ref_for_pid('loanid', loan_2.pid)},
        'patron': {'$ref': get_ref_for_pid('patrons', patron_martigny.pid)},
        'organisation': {'$ref': get_ref_for_pid('org', org_martigny.pid)},
        'status': 'open',
        'total_amount': 0.6,
        'type': 'overdue',
        'creation_date': datetime.now(timezone.utc).isoformat()
    }
    PatronTransaction.create(data, dbcommit=True, reindex=True)
    assert item_2 not in get_provisional_items_candidate_to_delete()
