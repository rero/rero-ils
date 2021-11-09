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

"""Tests complete workflow for the acquisition module."""

import mock
from api.acquisition.acq_utils import _make_resource
from invenio_accounts.testutils import login_user_via_session
from utils import VerifyRecordPermissionPatch, get_json, postdata

from rero_ils.modules.acq_order_lines.api import AcqOrderLine
from rero_ils.modules.acq_order_lines.models import AcqOrderLineStatus
from rero_ils.modules.acq_orders.api import AcqOrder, AcqOrderStatus
from rero_ils.modules.acq_orders.models import AcqOrderStatus
from rero_ils.modules.acq_receipts.models import AcqReceiptLineCreationStatus
from rero_ils.modules.notifications.api import Notification
from rero_ils.modules.notifications.models import NotificationChannel, \
    NotificationStatus, NotificationType, RecipientType
from rero_ils.modules.utils import get_ref_for_pid


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_acquisition_workflow(client, rero_json_header, org_martigny,
                              lib_martigny, lib_saxon, budget_2020_martigny,
                              vendor_martigny, librarian_martigny, document):
    """Test complete acquisition workflow."""
    def assert_account_data(manual_controls):
        """assert account information."""
        for record in manual_controls:
            account = record.get('name')
            assert account.expenditure_amount == \
                record.get('expenditure')
            assert account.encumbrance_amount == \
                record.get('encumbrance')
            assert account.remaining_balance == \
                record.get('balance')

    # STEP 1 :: Create root and childs accounts for martigny and saxon libs.
    martigny_root_account_data = {
        'name': 'Martigny root account',
        'number': 'MTY.0000.00',
        'allocated_amount': 10000,
        'budget': {'$ref': get_ref_for_pid('budg', budget_2020_martigny.pid)},
        'library': {'$ref': get_ref_for_pid('lib', lib_martigny.pid)}
    }
    martigny_root_account = _make_resource(
        client, 'acac', martigny_root_account_data)

    # STEP 2 :: Create child accounts for the martigny root account
    martigny_child_books_account_data = {
        'name': 'Martigny Books chid account',
        'number': 'MTY.000b.00',
        'allocated_amount': 2000,
        'budget': {'$ref': get_ref_for_pid('budg', budget_2020_martigny.pid)},
        'library': {'$ref': get_ref_for_pid('lib', lib_martigny.pid)},
        'parent': {'$ref': get_ref_for_pid('acac', martigny_root_account.pid)},
    }
    martigny_books_account = _make_resource(
        client, 'acac', martigny_child_books_account_data)

    martigny_child_serials_account_data = {
        'name': 'Martigny Serials chid account',
        'number': 'MTY.000s.00',
        'allocated_amount': 3000,
        'budget': {'$ref': get_ref_for_pid('budg', budget_2020_martigny.pid)},
        'library': {'$ref': get_ref_for_pid('lib', lib_martigny.pid)},
        'parent': {'$ref': get_ref_for_pid('acac', martigny_root_account.pid)},
    }
    martigny_serials_account = _make_resource(
        client, 'acac', martigny_child_serials_account_data)

    saxon_root_account_data = {
        'name': 'Saxon root account',
        'number': 'SXN.0000.00',
        'allocated_amount': 20000,
        'budget': {'$ref': get_ref_for_pid('budg', budget_2020_martigny.pid)},
        'library': {'$ref': get_ref_for_pid('lib', lib_saxon.pid)}
    }
    saxon_root_account = _make_resource(
        client, 'acac', saxon_root_account_data)

    saxon_child_books_account_data = {
        'name': 'Saxon Books chid account',
        'number': 'SXN.000b.00',
        'allocated_amount': 2500,
        'budget': {'$ref': get_ref_for_pid('budg', budget_2020_martigny.pid)},
        'library': {'$ref': get_ref_for_pid('lib', lib_saxon.pid)},
        'parent': {'$ref': get_ref_for_pid('acac', saxon_root_account.pid)},
    }
    saxon_books_account = _make_resource(
        client, 'acac', saxon_child_books_account_data)

    saxon_child_serials_account_data = {
        'name': 'Saxon Serials chid account',
        'number': 'SXN.000s.00',
        'allocated_amount': 4000,
        'budget': {'$ref': get_ref_for_pid('budg', budget_2020_martigny.pid)},
        'library': {'$ref': get_ref_for_pid('lib', lib_saxon.pid)},
        'parent': {'$ref': get_ref_for_pid('acac', saxon_root_account.pid)},
    }
    saxon_serials_account = _make_resource(
        client, 'acac', saxon_child_serials_account_data)

    manual_controls = [
            {
                'name': martigny_root_account,
                'balance': (5000, 10000),
                'expenditure': (0, 0),
                'encumbrance': (0, 0)
            },
            {
                'name': martigny_books_account,
                'balance': (2000, 2000),
                'expenditure': (0, 0),
                'encumbrance': (0, 0)
            },
            {
                'name': martigny_serials_account,
                'balance': (3000, 3000),
                'expenditure': (0, 0),
                'encumbrance': (0, 0)
            },
            {
                'name': saxon_root_account,
                'balance': (13500, 20000),
                'expenditure': (0, 0),
                'encumbrance': (0, 0)
            },
            {
                'name': saxon_books_account,
                'balance': (2500, 2500),
                'expenditure': (0, 0),
                'encumbrance': (0, 0)
            },
            {
                'name': saxon_serials_account,
                'balance': (4000, 4000),
                'expenditure': (0, 0),
                'encumbrance': (0, 0)
            }
    ]
    assert_account_data(manual_controls)

    # STEP 3 :: Create an order and order lines at the Martigny library
    login_user_via_session(client, librarian_martigny.user)
    # create the parent order record
    order_data = {
        'vendor': {'$ref': get_ref_for_pid('vndr', vendor_martigny.pid)},
        'library': {'$ref': get_ref_for_pid('lib', lib_martigny.pid)},
        'type': 'monograph',
    }
    order = _make_resource(client, 'acor', order_data)
    assert order['reference'] == f'ORDER-{order.pid}'
    assert order.get_order_total_amount() == 0
    assert order.status == AcqOrderStatus.PENDING
    assert order.can_delete
    # create order_lines for the parent order
    # 6 order lines are created as follows:
    # martigny_books_account:
    #       line_1: quantity: 5 of amount 10 = 50
    #       line_2: quantity: 2 of amount 50 = 100
    #       line_3: quantity: 3 of amount 100 = 300
    #                                         Total: 450
    # martigny_serials_account:
    #       line_1: quantity: 3 of amount 15 = 45
    #       line_2: quantity: 1 of amount 150 = 150
    #       line_3: quantity: 10 of amount 7 = 70
    #                                         Total: 265
    # order total = 450 + 165 = 715
    # order total quantities = 24
    order_line_data = {
        'acq_account': {
            '$ref': get_ref_for_pid('acac', martigny_books_account.pid)},
        'acq_order': {'$ref': get_ref_for_pid('acor', order.pid)},
        'document': {'$ref': get_ref_for_pid('doc', document.pid)},
        'quantity': 5,
        'amount': 10
    }
    books_order_line_1 = _make_resource(client, 'acol', order_line_data)
    assert books_order_line_1.get('total_amount') == 50
    assert not books_order_line_1.is_cancelled
    assert books_order_line_1.quantity == 5
    assert not books_order_line_1.received_quantity
    assert books_order_line_1.unreceived_quantity == 5
    assert books_order_line_1.status == AcqOrderLineStatus.APPROVED

    order_line_data = {
        'acq_account': {
            '$ref': get_ref_for_pid('acac', martigny_books_account.pid)},
        'acq_order': {'$ref': get_ref_for_pid('acor', order.pid)},
        'document': {'$ref': get_ref_for_pid('doc', document.pid)},
        'quantity': 2,
        'amount': 50
    }
    books_order_line_2 = _make_resource(client, 'acol', order_line_data)
    assert books_order_line_2.get('total_amount') == 100
    assert not books_order_line_2.is_cancelled
    assert books_order_line_2.quantity == 2
    assert not books_order_line_2.received_quantity
    assert books_order_line_2.unreceived_quantity == 2
    assert books_order_line_2.status == AcqOrderLineStatus.APPROVED

    order_line_data = {
        'acq_account': {
            '$ref': get_ref_for_pid('acac', martigny_books_account.pid)},
        'acq_order': {'$ref': get_ref_for_pid('acor', order.pid)},
        'document': {'$ref': get_ref_for_pid('doc', document.pid)},
        'quantity': 3,
        'amount': 100
    }
    books_order_line_3 = _make_resource(client, 'acol', order_line_data)
    assert books_order_line_3.get('total_amount') == 300
    assert not books_order_line_3.is_cancelled
    assert books_order_line_3.quantity == 3
    assert not books_order_line_3.received_quantity
    assert books_order_line_3.unreceived_quantity == 3
    assert books_order_line_3.status == AcqOrderLineStatus.APPROVED

    order_line_data = {
        'acq_account': {
            '$ref': get_ref_for_pid('acac', martigny_serials_account.pid)},
        'acq_order': {'$ref': get_ref_for_pid('acor', order.pid)},
        'document': {'$ref': get_ref_for_pid('doc', document.pid)},
        'quantity': 3,
        'amount': 15
    }
    serials_order_line_1 = _make_resource(client, 'acol', order_line_data)
    assert serials_order_line_1.get('total_amount') == 45
    assert not serials_order_line_1.is_cancelled
    assert serials_order_line_1.quantity == 3
    assert not serials_order_line_1.received_quantity
    assert serials_order_line_1.unreceived_quantity == 3
    assert serials_order_line_1.status == AcqOrderLineStatus.APPROVED

    order_line_data = {
        'acq_account': {
            '$ref': get_ref_for_pid('acac', martigny_serials_account.pid)},
        'acq_order': {'$ref': get_ref_for_pid('acor', order.pid)},
        'document': {'$ref': get_ref_for_pid('doc', document.pid)},
        'quantity': 1,
        'amount': 150
    }
    serials_order_line_2 = _make_resource(client, 'acol', order_line_data)
    assert serials_order_line_2.get('total_amount') == 150
    assert not serials_order_line_2.is_cancelled
    assert serials_order_line_2.quantity == 1
    assert not serials_order_line_2.received_quantity
    assert serials_order_line_2.unreceived_quantity == 1
    assert serials_order_line_2.status == AcqOrderLineStatus.APPROVED

    order_line_data = {
        'acq_account': {
            '$ref': get_ref_for_pid('acac', martigny_serials_account.pid)},
        'acq_order': {'$ref': get_ref_for_pid('acor', order.pid)},
        'document': {'$ref': get_ref_for_pid('doc', document.pid)},
        'quantity': 10,
        'amount': 7
    }
    serials_order_line_3 = _make_resource(client, 'acol', order_line_data)
    assert serials_order_line_3.get('total_amount') == 70
    assert not serials_order_line_3.is_cancelled
    assert serials_order_line_3.quantity == 10
    assert not serials_order_line_3.received_quantity
    assert serials_order_line_3.unreceived_quantity == 10
    assert serials_order_line_3.status == AcqOrderLineStatus.APPROVED

    # test order after adding lines
    assert order.get_order_total_amount() == 715
    assert order.status == AcqOrderStatus.PENDING
    # TODO: fix links to me for the order resource, this should fail
    assert order.can_delete
    assert not order.order_date
    assert order.item_quantity == 24
    assert not order.item_quantity_received

    manual_controls = [
        {
            'name': martigny_root_account,
            'balance': (5000, 9285),
            'expenditure': (0, 0),
            'encumbrance': (0, 715)
        },
        {
            'name': martigny_books_account,
            'balance': (1550, 1550),
            'expenditure': (0, 0),
            'encumbrance': (450, 0)
        },
        {
            'name': martigny_serials_account,
            'balance': (2735, 2735),
            'expenditure': (0, 0),
            'encumbrance': (265, 0)
        },
        {
            'name': saxon_root_account,
            'balance': (13500, 20000),
            'expenditure': (0, 0),
            'encumbrance': (0, 0)
        },
        {
            'name': saxon_books_account,
            'balance': (2500, 2500),
            'expenditure': (0, 0),
            'encumbrance': (0, 0)
        },
        {
            'name': saxon_serials_account,
            'balance': (4000, 4000),
            'expenditure': (0, 0),
            'encumbrance': (0, 0)
        }
    ]
    assert_account_data(manual_controls)

    # STEP 4 :: Cancel some order lines and change some quantities, make sure
    # calculations still good
    #
    # 6 order lines are created as follows:
    # martigny_books_account:
    #       line_1: quantity: 5 of amount 10 = 50
    #       line_2: quantity: 6 of amount 50 = 300  # changed  qty from 2 to 6
    #       line_3: quantity: 3 of amount 100 = 300 # cancelled
    #                                         Total: 350
    # martigny_serials_account:
    #       line_1: quantity: 3 of amount 15 = 45
    #       line_2: quantity: 2 of amount 150 = 300 # changed  qty from 1 to 2
    #       line_3: quantity: 10 of amount 7 = 70  # cancelled
    #                                         Total: 345
    # order total = 350 + 345 = 695
    # order total quantities = 16
    books_order_line_2['quantity'] = 6
    books_order_line_2.update(books_order_line_2, dbcommit=True, reindex=True)
    books_order_line_3['is_cancelled'] = True
    books_order_line_3.update(books_order_line_3, dbcommit=True, reindex=True)
    serials_order_line_2['quantity'] = 2
    serials_order_line_2.update(
        serials_order_line_2, dbcommit=True, reindex=True)
    serials_order_line_3['is_cancelled'] = True
    serials_order_line_3.update(
        serials_order_line_3, dbcommit=True, reindex=True)
    # ensure correct calculations and status again

    manual_controls = [
        {
            'name': martigny_root_account,
            'balance': (5000, 9305),
            'expenditure': (0, 0),
            'encumbrance': (0, 695)
        },
        {
            'name': martigny_books_account,
            'balance': (1650, 1650),
            'expenditure': (0, 0),
            'encumbrance': (350, 0)
        },
        {
            'name': martigny_serials_account,
            'balance': (2655, 2655),
            'expenditure': (0, 0),
            'encumbrance': (345, 0)
        },
        {
            'name': saxon_root_account,
            'balance': (13500, 20000),
            'expenditure': (0, 0),
            'encumbrance': (0, 0)
        },
        {
            'name': saxon_books_account,
            'balance': (2500, 2500),
            'expenditure': (0, 0),
            'encumbrance': (0, 0)
        },
        {
            'name': saxon_serials_account,
            'balance': (4000, 4000),
            'expenditure': (0, 0),
            'encumbrance': (0, 0)
        }
    ]
    assert_account_data(manual_controls)

    assert serials_order_line_3.get('total_amount') == 70
    assert serials_order_line_3.is_cancelled
    assert serials_order_line_3.quantity == 10
    assert not serials_order_line_3.received_quantity
    assert serials_order_line_3.unreceived_quantity == 10
    assert serials_order_line_3.status == AcqOrderLineStatus.CANCELLED

    assert serials_order_line_2.get('total_amount') == 300
    assert not serials_order_line_2.is_cancelled
    assert serials_order_line_2.quantity == 2
    assert not serials_order_line_2.received_quantity
    assert serials_order_line_2.unreceived_quantity == 2
    assert serials_order_line_2.status == AcqOrderLineStatus.APPROVED

    assert serials_order_line_1.get('total_amount') == 45
    assert not serials_order_line_1.is_cancelled
    assert serials_order_line_1.quantity == 3
    assert not serials_order_line_1.received_quantity
    assert serials_order_line_1.unreceived_quantity == 3
    assert serials_order_line_1.status == AcqOrderLineStatus.APPROVED

    assert books_order_line_3.get('total_amount') == 300
    assert books_order_line_3.is_cancelled
    assert books_order_line_3.quantity == 3
    assert not books_order_line_2.received_quantity
    assert books_order_line_3.unreceived_quantity == 3
    assert books_order_line_3.status == AcqOrderLineStatus.CANCELLED

    assert books_order_line_2.get('total_amount') == 300
    assert not books_order_line_2.is_cancelled
    assert books_order_line_2.quantity == 6
    assert not books_order_line_2.received_quantity
    assert books_order_line_2.unreceived_quantity == 6
    assert books_order_line_2.status == AcqOrderLineStatus.APPROVED

    assert books_order_line_1.get('total_amount') == 50
    assert not books_order_line_1.is_cancelled
    assert books_order_line_1.quantity == 5
    assert not books_order_line_1.received_quantity
    assert books_order_line_1.unreceived_quantity == 5
    assert books_order_line_1.status == AcqOrderLineStatus.APPROVED

    # STEP 5 :: Test send order and make sure statuses are up to date.
    address = vendor_martigny.get('default_contact').get('email')
    emails = [
        {'type': 'to', 'address': address},
        {'type': 'reply_to', 'address': lib_martigny.get('email')}
    ]
    res, data = postdata(
        client,
        'api_order.send_order',
        data=dict(emails=emails),
        url_data=dict(order_pid=order.pid)
    )
    data = get_json(res)
    assert res.status_code == 200

    for order_line in [
        {'line': books_order_line_1, 'status': AcqOrderLineStatus.ORDERED},
        {'line': books_order_line_2, 'status': AcqOrderLineStatus.ORDERED},
        {'line': books_order_line_3, 'status': AcqOrderLineStatus.CANCELLED},
        {'line': serials_order_line_1, 'status': AcqOrderLineStatus.ORDERED},
        {'line': serials_order_line_2, 'status': AcqOrderLineStatus.ORDERED},
        {'line': serials_order_line_3, 'status': AcqOrderLineStatus.CANCELLED},
    ]:
        line = AcqOrderLine.get_record_by_pid(order_line.get('line').pid)
        assert line.status == order_line.get('status')
        if order_line.get('status') == AcqOrderLineStatus.CANCELLED:
            assert not line.order_date
        else:
            assert line.order_date

    order = AcqOrder.get_record_by_pid(order.pid)
    assert order.status == AcqOrderStatus.ORDERED

    # notification testing
    notification_pid = data.get('data').get('pid')
    notif = Notification.get_record_by_pid(notification_pid)
    assert notif.organisation_pid == order.organisation_pid
    assert notif.aggregation_key == str(notif.id)
    assert notif.type == NotificationType.ACQUISITION_ORDER
    assert notif.status == NotificationStatus.DONE
    assert notif.acq_order_pid == order.pid
    assert notif.library_pid == order.library_pid
    assert notif.can_be_cancelled() == (False, None)
    assert notif.get_communication_channel() == NotificationChannel.EMAIL
    assert notif.get_language_to_use() == \
        vendor_martigny.get('communication_language')
    assert address in notif.get_recipients(RecipientType.TO)

    # STEP 6 :: Create the receipt parent record
    receipt_data = {
        'acq_order': {'$ref': get_ref_for_pid('acor', order.pid)},
        'exchange_rate': 1,
        'amount_adjustments': [
            {
                'label': 'handling fees',
                'amount': 2.0,
                'acq_account': {'$ref': get_ref_for_pid(
                    'acac', martigny_books_account.pid)}
            },
            {
                'label': 'discount',
                'amount': -1.0,
                'acq_account': {'$ref': get_ref_for_pid(
                    'acac', martigny_books_account.pid)}
            }
        ],
        'library': {'$ref': get_ref_for_pid('lib', lib_martigny.pid)},
        'organisation': {'$ref': get_ref_for_pid('org', org_martigny.pid)}
    }
    receipt_1 = _make_resource(client, 'acre', receipt_data)
    assert receipt_1.total_amount == 1
    assert receipt_1.can_delete

    # STEP 7 :: Receive some order lines
    # 6 order lines are created as follows:
    # martigny_books_account:
    #       line_1: quantity: 5 of amount 10 = 50
    #       line_2: quantity: 6 of amount 50 = 300  # changed  qty from 2 to 6
    #       line_3: quantity: 3 of amount 100 = 300 # cancelled
    #                                         Total: 350
    # martigny_serials_account:
    #       line_1: quantity: 3 of amount 15 = 45
    #       line_2: quantity: 2 of amount 150 = 300 # changed  qty from 1 to 2
    #       line_3: quantity: 10 of amount 7 = 70  # cancelled
    #                                         Total: 345
    # order total = 350 + 345 = 695
    # order total quantities = 16

    # partially receive one order with few quantities in receipt_1
    receipt_data_lines = [
        {
            "acq_order_line": {
                '$ref': get_ref_for_pid('acol', books_order_line_1.pid)},
            "amount": 10,
            "quantity": 2,
            "receipt_date": "2021-11-01"
        }
    ]
    res, data = postdata(
        client,
        'api_receipt.lines',
        data=receipt_data_lines,
        url_data=dict(receipt_pid=receipt_1.pid)
    )
    assert res.status_code == 200
    response = get_json(res).get('response')
    assert response[0]['status'] == AcqReceiptLineCreationStatus.SUCCESS

    # Test order and order lines
    for order_line in [
        {'line': books_order_line_1,
            'status': AcqOrderLineStatus.PARTIALLY_RECEIVED},
        {'line': books_order_line_2, 'status': AcqOrderLineStatus.ORDERED},
        {'line': books_order_line_3, 'status': AcqOrderLineStatus.CANCELLED},
        {'line': serials_order_line_1, 'status': AcqOrderLineStatus.ORDERED},
        {'line': serials_order_line_2, 'status': AcqOrderLineStatus.ORDERED},
        {'line': serials_order_line_3, 'status': AcqOrderLineStatus.CANCELLED}
    ]:
        line = AcqOrderLine.get_record_by_pid(order_line.get('line').pid)
        assert line.status == order_line.get('status')
    order = AcqOrder.get_record_by_pid(order.pid)
    assert order.status == AcqOrderStatus.PARTIALLY_RECEIVED

    manual_controls = [
        {
            'name': martigny_root_account,
            'balance': (5000, 9284),
            'expenditure': (0, 21),
            'encumbrance': (0, 695)
        },
        {
            'name': martigny_books_account,
            'balance': (1629, 1629),
            'expenditure': (21, 0),
            'encumbrance': (350, 0)
        },
        {
            'name': martigny_serials_account,
            'balance': (2655, 2655),
            'expenditure': (0, 0),
            'encumbrance': (345, 0)
        },
        {
            'name': saxon_root_account,
            'balance': (13500, 20000),
            'expenditure': (0, 0),
            'encumbrance': (0, 0)
        },
        {
            'name': saxon_books_account,
            'balance': (2500, 2500),
            'expenditure': (0, 0),
            'encumbrance': (0, 0)
        },
        {
            'name': saxon_serials_account,
            'balance': (4000, 4000),
            'expenditure': (0, 0),
            'encumbrance': (0, 0)
        }
    ]
    assert_account_data(manual_controls)

    # STEP 8 :: Receive the rest of order lines in a new receipt record
    # 6 order lines are created as follows:
    # martigny_books_account:
    #       line_1: quantity: 5 of amount 10 = 50
    #       line_2: quantity: 6 of amount 50 = 300  # changed  qty from 2 to 6
    #       line_3: quantity: 3 of amount 100 = 300 # cancelled
    #                                         Total: 350
    # martigny_serials_account:
    #       line_1: quantity: 3 of amount 15 = 45
    #       line_2: quantity: 2 of amount 150 = 300 # changed  qty from 1 to 2
    #       line_3: quantity: 10 of amount 7 = 70  # cancelled
    #                                         Total: 345
    # order total = 350 + 345 = 695
    # order total quantities = 16

    receipt_data_lines = [
        {
            "acq_order_line": {
                '$ref': get_ref_for_pid('acol', books_order_line_1.pid)},
            "amount": 10,
            "quantity": 3,
            "receipt_date": "2021-11-01"
        },
        {
            "acq_order_line": {
                '$ref': get_ref_for_pid('acol', books_order_line_2.pid)},
            "amount": 50,
            "quantity": 6,
            "receipt_date": "2021-11-01"
        },
        {
            "acq_order_line": {
                '$ref': get_ref_for_pid('acol', serials_order_line_1.pid)},
            "amount": 15,
            "quantity": 3,
            "receipt_date": "2021-11-01"
        },
        {
            "acq_order_line": {
                '$ref': get_ref_for_pid('acol', serials_order_line_2.pid)},
            "amount": 150,
            "quantity": 2,
            "receipt_date": "2021-11-01"
        }
    ]
    res, data = postdata(
        client,
        'api_receipt.lines',
        data=receipt_data_lines,
        url_data=dict(receipt_pid=receipt_1.pid)
    )
    assert res.status_code == 200
    response = get_json(res).get('response')
    assert response[0]['status'] == AcqReceiptLineCreationStatus.SUCCESS
    assert response[1]['status'] == AcqReceiptLineCreationStatus.SUCCESS
    assert response[2]['status'] == AcqReceiptLineCreationStatus.SUCCESS
    assert response[3]['status'] == AcqReceiptLineCreationStatus.SUCCESS

    # Test order and order lines
    for order_line in [
        {'line': books_order_line_1,
            'status': AcqOrderLineStatus.RECEIVED},
        {'line': books_order_line_2, 'status': AcqOrderLineStatus.RECEIVED},
        {'line': books_order_line_3, 'status': AcqOrderLineStatus.CANCELLED},
        {'line': serials_order_line_1, 'status': AcqOrderLineStatus.RECEIVED},
        {'line': serials_order_line_2, 'status': AcqOrderLineStatus.RECEIVED},
        {'line': serials_order_line_3, 'status': AcqOrderLineStatus.CANCELLED}
    ]:
        line = AcqOrderLine.get_record_by_pid(order_line.get('line').pid)
        assert line.status == order_line.get('status')
    order = AcqOrder.get_record_by_pid(order.pid)
    assert order.status == AcqOrderStatus.RECEIVED

    manual_controls = [
            {
                'name': martigny_root_account,
                'balance': (5000, 9304),
                'expenditure': (0, 696),
                'encumbrance': (0, 0)
            },
            {
                'name': martigny_books_account,
                'balance': (1649, 1649),
                'expenditure': (351, 0),
                'encumbrance': (0, 0)
            },
            {
                'name': martigny_serials_account,
                'balance': (2655, 2655),
                'expenditure': (345, 0),
                'encumbrance': (0, 0)
            },
            {
                'name': saxon_root_account,
                'balance': (13500, 20000),
                'expenditure': (0, 0),
                'encumbrance': (0, 0)
            },
            {
                'name': saxon_books_account,
                'balance': (2500, 2500),
                'expenditure': (0, 0),
                'encumbrance': (0, 0)
            },
            {
                'name': saxon_serials_account,
                'balance': (4000, 4000),
                'expenditure': (0, 0),
                'encumbrance': (0, 0)
            }
        ]
    assert_account_data(manual_controls)
