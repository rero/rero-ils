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

"""Tests scenario for acquisition accounts."""

import mock
import pytest
from api.acquisition.acq_utils import _del_resource, _make_resource
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from jsonschema.exceptions import ValidationError
from utils import VerifyRecordPermissionPatch, flush_index, get_json

from rero_ils.modules.acquisition.acq_accounts.api import AcqAccount, \
    AcqAccountsSearch
from rero_ils.modules.acquisition.acq_order_lines.api import AcqOrderLine
from rero_ils.modules.acquisition.acq_orders.api import AcqOrder
from rero_ils.modules.acquisition.acq_orders.models import AcqOrderStatus
from rero_ils.modules.api import IlsRecordError
from rero_ils.modules.utils import get_ref_for_pid


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_create_accounts(client, rero_json_header, org_martigny, lib_martigny,
                         budget_2020_martigny):
    """Basic scenario to test account creation."""
    # STEP 1 :: Create a root account
    root_account_data = {
        'name': 'Root account',
        'number': '000.0000.00',
        'allocated_amount': 1000,
        'budget': {'$ref': get_ref_for_pid('budg', budget_2020_martigny.pid)},
        'library': {'$ref': get_ref_for_pid('lib', lib_martigny.pid)}
    }
    root_account = _make_resource(client, 'acac', root_account_data)

    # STEP 2 :: Create a child account
    #   * Try to create a child account with too much amount regarding root
    #     account. It should be failed with a ValidationError due to
    #     `pre_create` extension.
    #   * Create a child account with 70% of the available amount of root
    #     account
    child_account_data = {
        'name': 'Chid account',
        'number': '000.0001.00',
        'allocated_amount': root_account['allocated_amount'] + 1,
        'budget': {'$ref': get_ref_for_pid('budg', budget_2020_martigny.pid)},
        'library': {'$ref': get_ref_for_pid('lib', lib_martigny.pid)},
        'parent': {'$ref': get_ref_for_pid('acac', root_account.pid)},
    }
    with pytest.raises(Exception) as excinfo:
        _make_resource(client, 'acac', child_account_data)
    assert 'Parent account available amount too low.' in str(excinfo.value)

    amount_70 = round(root_account['allocated_amount'] * 0.7)
    amount_30 = root_account['allocated_amount'] - amount_70
    child_account_data['allocated_amount'] = amount_70
    child_account = _make_resource(client, 'acac', child_account_data)

    # STEP 3 :: Check accounts distribution
    #   * Parent account should have 30% as available amount
    #   * Parent account distribution should be 70%
    assert root_account.remaining_balance[0] == amount_30
    assert root_account.distribution == amount_70

    # STEP 4 :: Decrease the allocated amount of parent account too much
    root_account_data['allocated_amount'] = amount_30 + 1
    with pytest.raises(Exception) as excinfo:
        root_account.update(root_account_data, dbcommit=True)
    assert 'Remaining balance too low' in str(excinfo.value)

    # RESET DATA
    _del_resource(client, 'acac', child_account.pid)
    _del_resource(client, 'acac', root_account.pid)


# DEV NOTES : This mock will prevent any translations problems to occurs
#             When a translation is done, then the input string will be return
#             without any changes.
@mock.patch('rero_ils.modules.acquisition.acq_accounts.api._',
            mock.MagicMock(side_effect=lambda v: v))
def test_transfer_funds_api(client, rero_json_header, org_martigny,
                            lib_martigny, budget_2020_martigny,
                            librarian_martigny):
    """Scenario to test fund transfer between both accounts."""

    def _check_account(account):
        """Check amount available about an account."""
        return account['allocated_amount'], account.remaining_balance[0]

    login_user_via_session(client, librarian_martigny.user)

    # STEP 0 :: Create account tree
    #   Test structure account is described below. Each account are noted like
    #   A{x, y} where :
    #     * 'A' is the account name
    #     * 'x' is the account allocated amount
    #     * 'y' is the account remaining_balance
    #
    #   A{2000, 500}                E{200, 100}
    #   |-- B{500, 150}             +-- F{200, 100}
    #   |   |-- B1{300, 300}            +-- G{100, 100}
    #   |   +-- B2{50, 50}
    #   +-- C{1000, 700}
    #       |-- C1{100, 100}
    #       |-- C2{100, 30}
    #       |   |-- C21{50, 50}
    #       |   +-- C22{20, 20}
    #       +-- C3{100, 100}
    basic_data = {
        'allocated_amount': 1000,
        'budget': {'$ref': get_ref_for_pid('budg', budget_2020_martigny.pid)},
        'library': {'$ref': get_ref_for_pid('lib', lib_martigny.pid)}
    }
    account_a = dict(name='A', allocated_amount=2000)
    account_a = {**basic_data, **account_a}
    account_a = _make_resource(client, 'acac', account_a)
    a_ref = {'$ref': get_ref_for_pid('acac', account_a.pid)}

    account_b = dict(name='B', allocated_amount=500, parent=a_ref)
    account_b = {**basic_data, **account_b}
    account_b = _make_resource(client, 'acac', account_b)
    b_ref = {'$ref': get_ref_for_pid('acac', account_b.pid)}

    account_c = dict(name='C', allocated_amount=1000, parent=a_ref)
    account_c = {**basic_data, **account_c}
    account_c = _make_resource(client, 'acac', account_c)
    c_ref = {'$ref': get_ref_for_pid('acac', account_c.pid)}

    account_b1 = dict(name='B1', allocated_amount=300, parent=b_ref)
    account_b1 = {**basic_data, **account_b1}
    account_b1 = _make_resource(client, 'acac', account_b1)
    account_b2 = dict(name='B2', allocated_amount=50, parent=b_ref)
    account_b2 = {**basic_data, **account_b2}
    account_b2 = _make_resource(client, 'acac', account_b2)

    account_c1 = dict(name='C1', allocated_amount=100, parent=c_ref)
    account_c1 = {**basic_data, **account_c1}
    account_c1 = _make_resource(client, 'acac', account_c1)
    account_c2 = dict(name='C2', allocated_amount=100, parent=c_ref)
    account_c2 = {**basic_data, **account_c2}
    account_c2 = _make_resource(client, 'acac', account_c2)
    account_c3 = dict(name='C3', allocated_amount=100, parent=c_ref)
    account_c3 = {**basic_data, **account_c3}
    account_c3 = _make_resource(client, 'acac', account_c3)
    c2_ref = {'$ref': get_ref_for_pid('acac', account_c2.pid)}

    account_c21 = dict(name='C21', allocated_amount=50, parent=c2_ref)
    account_c21 = {**basic_data, **account_c21}
    account_c21 = _make_resource(client, 'acac', account_c21)
    account_c22 = dict(name='C22', allocated_amount=20, parent=c2_ref)
    account_c22 = {**basic_data, **account_c22}
    account_c22 = _make_resource(client, 'acac', account_c22)

    account_e = dict(name='E', allocated_amount=300)
    account_e = {**basic_data, **account_e}
    account_e = _make_resource(client, 'acac', account_e)
    e_ref = {'$ref': get_ref_for_pid('acac', account_e.pid)}

    account_f = dict(name='F', allocated_amount=200, parent=e_ref)
    account_f = {**basic_data, **account_f}
    account_f = _make_resource(client, 'acac', account_f)
    f_ref = {'$ref': get_ref_for_pid('acac', account_f.pid)}

    account_g = dict(name='G', allocated_amount=100, parent=f_ref)
    account_g = {**basic_data, **account_g}
    account_g = _make_resource(client, 'acac', account_g)

    # TEST 0 :: Try the API with invalid arguments.
    res = client.get(url_for('api_acq_account.transfer_funds'))
    assert res.status_code == 400
    assert 'argument is required' in res.get_data(as_text=True)
    cases_to_test = [{
        'source': 'dummy', 'target': 'dummy', 'amount': 'dummy',
        'error': 'Unable to load source account'
    }, {
        'source': account_a.pid, 'target': 'dummy', 'amount': 'dummy',
        'error': 'Unable to load target account'
    }, {
        'source': account_a.pid, 'target': account_b.pid, 'amount': 'dummy',
        'error': "could not convert"
    }, {
        'source': account_a.pid, 'target': account_b.pid, 'amount': -1.52,
        'error': "'amount' should be a positive number"
    }, {
        'source': account_a.pid, 'target': account_a.pid, 'amount': 1,
        'error': "Cannot transfer fund to myself"
    }, {
        'source': account_a.pid, 'target': account_e.pid, 'amount': 100000,
        'error': "Not enough available money from source account"
    }]
    for case in cases_to_test:
        res = client.get(url_for(
            'api_acq_account.transfer_funds',
            source=case['source'], target=case['target'], amount=case['amount']
        ))
        assert res.status_code == 400
        data = get_json(res)
        assert case['error'] in data['message']

    # STATUS BEFORE NEXT TEST
    #   A{2000, 500}                E{300, 100}
    #   |-- B{500, 150}             +-- F{200, 100}
    #   |   |-- B1{300, 300}            +-- G{100, 100}
    #   |   +-- B2{50, 50}
    #   +-- C{1000, 700}
    #       |-- C1{100, 100}
    #       |-- C2{100, 30}
    #       |   |-- C21{50, 50}
    #       |   +-- C22{20, 20}
    #       +-- C3{100, 100}

    # TEST 1 :: Transfer to an ancestor account
    #   Transfer 25 from C21 account to C account. After this transfer, the
    #   C20 remaining balance should be equal to 25 ; the remaining balance for
    #   C account should be 725
    res = client.get(url_for(
        'api_acq_account.transfer_funds',
        source=account_c21.pid, target=account_c.pid, amount=25
    ))
    assert res.status_code == 200
    account_c21 = AcqAccount.get_record_by_pid(account_c21.pid)
    account_c2 = AcqAccount.get_record_by_pid(account_c2.pid)
    account_c = AcqAccount.get_record_by_pid(account_c.pid)
    assert _check_account(account_c) == (1000, 725)
    assert _check_account(account_c2) == (75, 30)
    assert _check_account(account_c21) == (25, 25)

    # STATUS BEFORE NEXT TEST
    #   A{2000, 500}                E{300, 100}
    #   |-- B{500, 150}             +-- F{200, 100}
    #   |   |-- B1{300, 300}            +-- G{100, 100}
    #   |   +-- B2{50, 50}
    #   +-- C{1000, 725}
    #       |-- C1{100, 100}
    #       |-- C2{75, 30}
    #       |   |-- C21{25, 25}
    #       |   +-- C22{20, 20}
    #       +-- C3{100, 100}

    # TEST 2 :: Transfer between accounts in the same tree
    #   Transfer 100 from A account to C22 account. After this transfer, the
    #   C22 remaining balance should be equal to 120 ; the remaining balance
    #   for A account should be 400. The remaining balance for intermediate
    #   accounts (C, C2) should be the same, but allocated amount should be
    #   increased by 100 (1100, 175)
    res = client.get(url_for(
        'api_acq_account.transfer_funds',
        source=account_a.pid, target=account_c22.pid, amount=100
    ))
    assert res.status_code == 200
    account_a = AcqAccount.get_record_by_pid(account_a.pid)
    account_c = AcqAccount.get_record_by_pid(account_c.pid)
    account_c2 = AcqAccount.get_record_by_pid(account_c2.pid)
    account_c22 = AcqAccount.get_record_by_pid(account_c22.pid)
    assert _check_account(account_a) == (2000, 400)
    assert _check_account(account_c) == (1100, 725)
    assert _check_account(account_c2) == (175, 30)
    assert _check_account(account_c22) == (120, 120)

    # STATUS BEFORE NEXT TEST
    #   A{2000, 400}                E{300, 100}
    #   |-- B{500, 150}             +-- F{200, 100}
    #   |   |-- B1{300, 300}            +-- G{100, 100}
    #   |   +-- B2{50, 50}
    #   +-- C{1100, 725}
    #       |-- C1{100, 100}
    #       |-- C2{175, 30}
    #       |   |-- C21{25, 25}
    #       |   +-- C22{120, 120}
    #       +-- C3{100, 100}

    # TEST 3 :: Transfer 300 from B1 account to C21 account.
    #   Same behavior than previous test, but source account isn't the common
    #   ancestor.
    res = client.get(url_for(
        'api_acq_account.transfer_funds',
        source=account_b1.pid, target=account_c21.pid, amount=300
    ))
    assert res.status_code == 200
    account_b1 = AcqAccount.get_record_by_pid(account_b1.pid)
    account_b = AcqAccount.get_record_by_pid(account_b.pid)
    account_a = AcqAccount.get_record_by_pid(account_a.pid)
    account_c = AcqAccount.get_record_by_pid(account_c.pid)
    account_c2 = AcqAccount.get_record_by_pid(account_c2.pid)
    account_c21 = AcqAccount.get_record_by_pid(account_c21.pid)
    assert _check_account(account_b1) == (0, 0)
    assert _check_account(account_b) == (200, 150)
    assert _check_account(account_a) == (2000, 400)
    assert _check_account(account_c) == (1400, 725)
    assert _check_account(account_c2) == (475, 30)
    assert _check_account(account_c21) == (325, 325)

    # STATUS BEFORE NEXT TEST
    #   A{2000, 400}                E{300, 100}
    #   |-- B{200, 150}             +-- F{200, 100}
    #   |   |-- B1{0, 0}                +-- G{100, 100}
    #   |   +-- B2{50, 50}
    #   +-- C{1400, 725}
    #       |-- C1{100, 100}
    #       |-- C2{475, 30}
    #       |   |-- C21{325, 325}
    #       |   +-- C22{120, 120}
    #       +-- C3{100, 100}

    # TEST 4 :: Transfer between two account from separate tree.
    #   We transfer 100 from F account to C3 account. As both accounts aren't
    #   in the same tree, they not exists a common ancestor. Each root tag
    #   should be update (E will decrease, A will increase)
    res = client.get(url_for(
        'api_acq_account.transfer_funds',
        source=account_f.pid, target=account_c3.pid, amount=100
    ))
    assert res.status_code == 200
    account_f = AcqAccount.get_record_by_pid(account_f.pid)
    account_e = AcqAccount.get_record_by_pid(account_e.pid)
    account_a = AcqAccount.get_record_by_pid(account_a.pid)
    account_c = AcqAccount.get_record_by_pid(account_c.pid)
    account_c3 = AcqAccount.get_record_by_pid(account_c3.pid)
    assert _check_account(account_f) == (100, 0)
    assert _check_account(account_e) == (200, 100)
    assert _check_account(account_a) == (2100, 400)
    assert _check_account(account_c) == (1500, 725)
    assert _check_account(account_c3) == (200, 200)

    # STATUS BEFORE NEXT TEST
    #   A{2100, 400}                E{200, 100}
    #   |-- B{200, 150}             +-- F{100, 0}
    #   |   |-- B1{0, 0}                +-- G{100, 100}
    #   |   +-- B2{50, 50}
    #   +-- C{1500, 725}
    #       |-- C1{100, 100}
    #       |-- C2{475, 30}
    #       |   |-- C21{325, 325}
    #       |   +-- C22{120, 120}
    #       +-- C3{200, 200}

    # delete accounts
    _del_resource(client, 'acac', account_g.pid)
    _del_resource(client, 'acac', account_f.pid)
    _del_resource(client, 'acac', account_e.pid)

    _del_resource(client, 'acac', account_c22.pid)
    _del_resource(client, 'acac', account_c21.pid)
    _del_resource(client, 'acac', account_c3.pid)
    _del_resource(client, 'acac', account_c2.pid)
    _del_resource(client, 'acac', account_c1.pid)
    _del_resource(client, 'acac', account_c.pid)
    _del_resource(client, 'acac', account_b2.pid)
    _del_resource(client, 'acac', account_b1.pid)
    _del_resource(client, 'acac', account_b.pid)
    _del_resource(client, 'acac', account_a.pid)


def test_acquisition_order(
    client, rero_json_header, org_martigny, lib_martigny, budget_2020_martigny,
    vendor_martigny, librarian_martigny, document
):
    """Scenario to test orders creation."""

    login_user_via_session(client, librarian_martigny.user)

    # STEP 0 :: Create the account tree
    basic_data = {
        'allocated_amount': 1000,
        'budget': {'$ref': get_ref_for_pid('budg', budget_2020_martigny.pid)},
        'library': {'$ref': get_ref_for_pid('lib', lib_martigny.pid)}
    }
    account_a = dict(name='A', allocated_amount=2000)
    account_a = {**basic_data, **account_a}
    account_a = _make_resource(client, 'acac', account_a)
    account_a_ref = {'$ref': get_ref_for_pid('acac', account_a.pid)}

    account_b = dict(name='B', allocated_amount=500, parent=account_a_ref)
    account_b = {**basic_data, **account_b}
    account_b = _make_resource(client, 'acac', account_b)
    account_b_ref = {'$ref': get_ref_for_pid('acac', account_b.pid)}

    # TEST 1 :: Create an order and add some order lines on it.
    #   * The creation of the order will be successful
    #   * We create first order line linked to account B. After this creation,
    #     we can check the encumbrance of this account and its parent account.
    order_data = {
        'vendor': {'$ref': get_ref_for_pid('vndr', vendor_martigny.pid)},
        'library': {'$ref': get_ref_for_pid('lib', lib_martigny.pid)},
        'type': 'monograph',
    }
    order = _make_resource(client, 'acor', order_data)
    assert order['reference'] == f'ORDER-{order.pid}'
    assert order.get_order_provisional_total_amount() == 0
    assert order.status == AcqOrderStatus.PENDING
    assert order.can_delete

    basic_data = {
        'acq_account': account_b_ref,
        'acq_order': {'$ref': get_ref_for_pid('acor', order.pid)},
        'document': {'$ref': get_ref_for_pid('doc', document.pid)},
        'quantity': 4,
        'amount': 25
    }
    order_line_1 = _make_resource(client, 'acol', basic_data)
    assert order_line_1.get('total_amount') == 100

    assert account_b.encumbrance_amount[0] == 100
    assert account_b.remaining_balance[0] == 400  # 500 - 100
    assert account_a.encumbrance_amount == (0, 100)
    assert account_a.remaining_balance[0] == 1500
    assert account_a.expenditure_amount == (0, 0)

    # TEST 2 :: update the number of received item from the order line.
    #   * The encumbrance amount account should be decrease by quantity
    #     received * amount.
    # field received_quantity is now dynamically calculated at the receive of
    # receipt_lines
    assert order_line_1.received_quantity == 0

    # TEST 3 :: add a new cancelled order line.
    #   * As this new order line has CANCELLED status, its amount is not
    #     calculated into the encumbrance_amount
    basic_data = {
        'acq_account': account_b_ref,
        'acq_order': {'$ref': get_ref_for_pid('acor', order.pid)},
        'document': {'$ref': get_ref_for_pid('doc', document.pid)},
        'quantity': 2,
        'amount': 10,
        'is_cancelled': True
    }
    order_line_1_1 = _make_resource(client, 'acol', basic_data)
    assert order_line_1_1.get('total_amount') == 20

    assert account_b.encumbrance_amount[0] == 100
    assert account_b.remaining_balance[0] == 400  # 500 - 100
    assert account_a.encumbrance_amount == (0, 100)
    assert account_a.remaining_balance[0] == 1500
    assert account_a.expenditure_amount == (0, 0)

    # TEST 4 :: new order line raises the limit of account available money.
    #   * Create a new order line on the same account ; but the total amount
    #     of the line must be larger than account available money --> should
    #     be raise an ValidationError
    #   * Update the first order line to raise the limit and check than the
    #     same validation error occurs.
    #   * Update the first order line to reach the limit without exceeding it
    order_line_2 = dict(quantity=50)
    order_line_2 = {**basic_data, **order_line_2}
    with pytest.raises(Exception) as excinfo:
        _make_resource(client, 'acol', order_line_2)
    assert 'Parent account available amount too low' in str(excinfo.value)

    order_line_1['quantity'] = 50
    with pytest.raises(Exception) as excinfo:
        order_line_1.update(order_line_1, dbcommit=True, reindex=True)
    assert 'Parent account available amount too low' in str(excinfo.value)

    order_line_1['quantity'] = 20
    order_line_1 = order_line_1.update(order_line_1, dbcommit=True,
                                       reindex=True)
    assert account_b.encumbrance_amount[0] == 500
    assert account_b.remaining_balance[0] == 0
    assert account_a.encumbrance_amount == (0, 500)
    assert account_a.remaining_balance[0] == 1500

    # TEST 5 :: Update the account encumbrance exceedance and test it.
    #   * At this time, the account B doesn't have any available money to
    #     place any nex order line. Try to add an other item to existing order
    #     line will raise a ValidationError
    #   * Update the account 'encumbrance_exceedance' setting to allow more
    #     encumbrance and try to add an item to order_line. It will be OK
    order_line_1['quantity'] += 1
    with pytest.raises(Exception) as excinfo:
        order_line_1.update(order_line_1, dbcommit=True, reindex=True)
    assert 'Parent account available amount too low' in str(excinfo.value)

    account_b['encumbrance_exceedance'] = 5  # 5% of 500 = 25
    account_b = account_b.update(account_b, dbcommit=True, reindex=True)
    order_line_1 = order_line_1.update(order_line_1, dbcommit=True,
                                       reindex=True)
    assert account_b.encumbrance_amount[0] == 525
    assert account_b.remaining_balance[0] == -25
    assert account_a.encumbrance_amount == (0, 525)
    assert account_a.remaining_balance[0] == 1500

    # Test cascade deleting of order lines when attempting to delete a
    # PENDING order.
    order_line_1 = AcqOrderLine.get_record_by_pid(order_line_1.pid)
    order_line_1['is_cancelled'] = True
    order_line_1.update(order_line_1, dbcommit=True, reindex=True)

    order = AcqOrder.get_record_by_pid(order.pid)
    assert order.status == AcqOrderStatus.CANCELLED

    # Delete CANCELLED order is not permitted
    with pytest.raises(IlsRecordError.NotDeleted):
        _del_resource(client, 'acor', order.pid)

    order_line_1['is_cancelled'] = False
    order_line_1.update(order_line_1, dbcommit=True, reindex=True)

    order = AcqOrder.get_record_by_pid(order.pid)
    assert order.status == AcqOrderStatus.PENDING

    # DELETE created resources
    _del_resource(client, 'acor', order.pid)
    # Deleting the parent PENDING order does delete all of its order lines
    order_line_1 = AcqOrderLine.get_record_by_pid(order_line_1.pid)
    order_line_1_1 = AcqOrderLine.get_record_by_pid(order_line_1_1.pid)
    assert not order_line_1
    assert not order_line_1_1

    _del_resource(client, 'acac', account_b.pid)
    _del_resource(client, 'acac', account_a.pid)


def test_acquisition_order_line_account_changes(
    client, rero_json_header, org_martigny, lib_martigny, budget_2020_martigny,
    vendor_martigny, librarian_martigny, document
):
    """Test validation behavior on if related account of order line changes."""

    # We will create an order line related to a first account (acc#A) ; then
    # we updated the related account (acc#B). We need to check if :
    #  - the destination account has enough balance to accept this order_line
    #  - both account ES hits are correct (encumbrance, balance, ...) after
    #    this change.

    login_user_via_session(client, librarian_martigny.user)

    # STEP 0 :: Init the acquisition structure
    #   1) create two independent accounts
    #   2) create an order
    #   3) add an order line related to the acc#A
    #   4) check if balance/encumbrance are correct into ES indexes.
    basic_data = {
        'allocated_amount': 0,
        'budget': {'$ref': get_ref_for_pid('budg', budget_2020_martigny.pid)},
        'library': {'$ref': get_ref_for_pid('lib', lib_martigny.pid)}
    }
    account_a = dict(name='A', allocated_amount=1000)
    account_a = _make_resource(client, 'acac', {**basic_data, **account_a})
    account_a_ref = {'$ref': get_ref_for_pid('acac', account_a.pid)}

    account_b = dict(name='B')
    account_b = _make_resource(client, 'acac', {**basic_data, **account_b})
    account_b_ref = {'$ref': get_ref_for_pid('acac', account_b.pid)}

    order = _make_resource(client, 'acor', {
        'vendor': {'$ref': get_ref_for_pid('vndr', vendor_martigny.pid)},
        'library': {'$ref': get_ref_for_pid('lib', lib_martigny.pid)},
        'type': 'monograph',
    })
    order_line = _make_resource(client, 'acol', {
        'acq_account': account_a_ref,
        'acq_order': {'$ref': get_ref_for_pid('acor', order.pid)},
        'document': {'$ref': get_ref_for_pid('doc', document.pid)},
        'quantity': 2,
        'amount': 100
    })

    assert account_a.encumbrance_amount == (200, 0)
    assert account_a.remaining_balance == (800, 800)
    assert account_b.encumbrance_amount == (0, 0)
    assert account_b.remaining_balance == (0, 0)

    # STEP 1 :: Change account related to the order line
    #    Staff member did a bad manipulation ! the order line should be related
    #    to the acc#B (not the acc#A). It will try to change that. But
    #    validation problem should occur because the remaining balance for this
    #    account isn't correct to accept this order_line.
    order_line['acq_account'] = account_b_ref
    with pytest.raises(ValidationError) as err:
        order_line.update(order_line, dbcommit=True, reindex=True)
    assert 'Parent account available amount too low' in str(err)
    order_line = AcqOrderLine.get_record(order_line.id)
    assert order_line.account_pid == account_a.pid

    # STEP 2 :: Set more money on destination account
    #   Staff member add some money on the destination account to accept this
    #   order line. We update the order line again and check that balance of
    #   original and destination account are correct.
    account_b['allocated_amount'] = 1000
    account_b = account_b.update(account_b, dbcommit=True, reindex=True)
    order_line['acq_account'] = account_b_ref
    order_line = order_line.update(order_line, dbcommit=True, reindex=True)
    flush_index(AcqAccountsSearch.Meta.index)
    assert order_line.account_pid == account_b.pid
    assert account_a.encumbrance_amount == (0, 0)
    assert account_a.remaining_balance == (1000, 1000)
    assert account_b.encumbrance_amount == (200, 0)
    assert account_b.remaining_balance == (800, 800)

    # RESET FIXTURES
    _del_resource(client, 'acol', order_line.pid)
    _del_resource(client, 'acor', order.pid)
    _del_resource(client, 'acac', account_b.pid)
    _del_resource(client, 'acac', account_a.pid)
