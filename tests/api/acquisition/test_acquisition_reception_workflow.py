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
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import VerifyRecordPermissionPatch, postdata

from rero_ils.modules.acquisition.acq_order_lines.api import AcqOrderLine
from rero_ils.modules.acquisition.acq_order_lines.models import \
    AcqOrderLineStatus
from rero_ils.modules.acquisition.acq_orders.api import AcqOrder
from rero_ils.modules.acquisition.acq_orders.models import AcqOrderStatus
from rero_ils.modules.acquisition.acq_receipt_lines.api import \
    AcqReceiptLinesSearch
from rero_ils.modules.acquisition.acq_receipts.api import AcqReceipt, \
    AcqReceiptLine, AcqReceiptsSearch
from rero_ils.modules.acquisition.acq_receipts.models import \
    AcqReceiptLineCreationStatus
from rero_ils.modules.notifications.api import Notification
from rero_ils.modules.notifications.models import NotificationChannel, \
    NotificationStatus, NotificationType, RecipientType
from rero_ils.modules.utils import get_ref_for_pid
from rero_ils.modules.vendors.models import VendorContactType


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_acquisition_reception_workflow(
    client, rero_json_header, org_martigny,
    lib_martigny, lib_saxon, budget_2020_martigny,
    vendor_martigny, librarian_martigny, document
):
    """Test complete acquisition workflow."""

    def assert_account_data(accounts):
        """assert account informations."""
        for acc, (balance, expenditure, encumbrance) in accounts.items():
            assert acc.expenditure_amount == expenditure
            assert acc.encumbrance_amount == encumbrance
            assert acc.remaining_balance == balance

    # STEP 1 :: Create account structures
    #   * Create accounts for Martigny library.
    #     - MTY.0000.00' (root)
    #       --> MTY.000b.00
    #       --> MTY.000s.00
    #   * Create accounts for Saxon library.
    #     - SXN.0000.00 (root)
    #       --> SXN.000b.00
    #       --> SXN.000s.00
    data = {
        'name': 'Martigny root account',
        'number': 'MTY.0000.00',
        'allocated_amount': 10000,
        'budget': {'$ref': get_ref_for_pid('budg', budget_2020_martigny.pid)},
        'library': {'$ref': get_ref_for_pid('lib', lib_martigny.pid)}
    }
    m_root_acc = _make_resource(client, 'acac', data)
    data = {
        'name': 'Martigny Books child account',
        'number': 'MTY.000b.00',
        'allocated_amount': 2000,
        'budget': {'$ref': get_ref_for_pid('budg', budget_2020_martigny.pid)},
        'library': {'$ref': get_ref_for_pid('lib', lib_martigny.pid)},
        'parent': {'$ref': get_ref_for_pid('acac', m_root_acc.pid)},
    }
    m_books_acc = _make_resource(client, 'acac', data)
    data = {
        'name': 'Martigny Serials child account',
        'number': 'MTY.000s.00',
        'allocated_amount': 3000,
        'budget': {'$ref': get_ref_for_pid('budg', budget_2020_martigny.pid)},
        'library': {'$ref': get_ref_for_pid('lib', lib_martigny.pid)},
        'parent': {'$ref': get_ref_for_pid('acac', m_root_acc.pid)},
    }
    m_serials_acc = _make_resource(client, 'acac', data)
    data = {
        'name': 'Saxon root account',
        'number': 'SXN.0000.00',
        'allocated_amount': 20000,
        'budget': {'$ref': get_ref_for_pid('budg', budget_2020_martigny.pid)},
        'library': {'$ref': get_ref_for_pid('lib', lib_saxon.pid)}
    }
    s_root_acc = _make_resource(client, 'acac', data)
    data = {
        'name': 'Saxon Books chid account',
        'number': 'SXN.000b.00',
        'allocated_amount': 2500,
        'budget': {'$ref': get_ref_for_pid('budg', budget_2020_martigny.pid)},
        'library': {'$ref': get_ref_for_pid('lib', lib_saxon.pid)},
        'parent': {'$ref': get_ref_for_pid('acac', s_root_acc.pid)},
    }
    s_books_acc = _make_resource(client, 'acac', data)
    data = {
        'name': 'Saxon Serials chid account',
        'number': 'SXN.000s.00',
        'allocated_amount': 4000,
        'budget': {'$ref': get_ref_for_pid('budg', budget_2020_martigny.pid)},
        'library': {'$ref': get_ref_for_pid('lib', lib_saxon.pid)},
        'parent': {'$ref': get_ref_for_pid('acac', s_root_acc.pid)},
    }
    s_serials_acc = _make_resource(client, 'acac', data)

    # For each account check data. the dict values are tuples. Each tuple
    # define `balance`, `expenditure`, `encumbrance`
    manual_controls = {
        m_root_acc: ((5000, 10000), (0, 0), (0, 0)),
        m_books_acc: ((2000, 2000), (0, 0), (0, 0)),
        m_serials_acc: ((3000, 3000), (0, 0), (0, 0)),
        s_root_acc: ((13500, 20000), (0, 0), (0, 0)),
        s_books_acc: ((2500, 2500), (0, 0), (0, 0)),
        s_serials_acc: ((4000, 4000), (0, 0), (0, 0))
    }
    assert_account_data(manual_controls)

    # STEP 2 :: CREATE REAL ORDER
    #   * Create an order for Martigny library
    #   * Adds 6 order lines for this order
    #       martigny_books_account:
    #           line_1: quantity: 5 of amount 10   = 50
    #           line_2: quantity: 2 of amount 50   = 100
    #           line_3: quantity: 3 of amount 100  = 300
    #                                        Total = 450
    #       martigny_serials_account:
    #           line_1: quantity: 3 of amount 15   = 45
    #           line_2: quantity: 1 of amount 150  = 150
    #           line_3: quantity: 10 of amount 7   = 70
    #                                        Total = 265
    #       Items quantity = 24: order total amount = 715
    login_user_via_session(client, librarian_martigny.user)
    data = {
        'vendor': {'$ref': get_ref_for_pid('vndr', vendor_martigny.pid)},
        'library': {'$ref': get_ref_for_pid('lib', lib_martigny.pid)},
        'type': 'monograph',
    }
    order = _make_resource(client, 'acor', data)
    assert order['reference'] == f'ORDER-{order.pid}'
    assert order.get_order_provisional_total_amount() == 0
    assert order.status == AcqOrderStatus.PENDING
    assert order.can_delete

    data = {
        'acq_account': {'$ref': get_ref_for_pid('acac', m_books_acc.pid)},
        'acq_order': {'$ref': get_ref_for_pid('acor', order.pid)},
        'document': {'$ref': get_ref_for_pid('doc', document.pid)},
        'quantity': 5,
        'amount': 10
    }
    order_line_1 = _make_resource(client, 'acol', data)
    order_line_1_ref = get_ref_for_pid('acol', order_line_1.pid)
    assert order_line_1.get('total_amount') == 50
    assert order_line_1.quantity == 5
    assert order_line_1.received_quantity == 0
    assert order_line_1.unreceived_quantity == 5
    assert not order_line_1.is_cancelled
    assert order_line_1.status == AcqOrderLineStatus.APPROVED

    data = {
        'acq_account': {'$ref': get_ref_for_pid('acac', m_books_acc.pid)},
        'acq_order': {'$ref': get_ref_for_pid('acor', order.pid)},
        'document': {'$ref': get_ref_for_pid('doc', document.pid)},
        'quantity': 2,
        'amount': 50
    }
    order_line_2 = _make_resource(client, 'acol', data)
    order_line_2_ref = get_ref_for_pid('acol', order_line_2.pid)
    assert order_line_2.get('total_amount') == 100
    assert order_line_2.quantity == 2
    assert order_line_2.received_quantity == 0
    assert order_line_2.unreceived_quantity == 2
    assert not order_line_2.is_cancelled
    assert order_line_2.status == AcqOrderLineStatus.APPROVED

    data = {
        'acq_account': {'$ref': get_ref_for_pid('acac', m_books_acc.pid)},
        'acq_order': {'$ref': get_ref_for_pid('acor', order.pid)},
        'document': {'$ref': get_ref_for_pid('doc', document.pid)},
        'quantity': 3,
        'amount': 100
    }
    order_line_3 = _make_resource(client, 'acol', data)
    order_line_3_ref = get_ref_for_pid('acol', order_line_3.pid)
    assert order_line_3.get('total_amount') == 300
    assert order_line_3.quantity == 3
    assert order_line_3.received_quantity == 0
    assert order_line_3.unreceived_quantity == 3
    assert not order_line_3.is_cancelled
    assert order_line_3.status == AcqOrderLineStatus.APPROVED

    data = {
        'acq_account': {'$ref': get_ref_for_pid('acac', m_serials_acc.pid)},
        'acq_order': {'$ref': get_ref_for_pid('acor', order.pid)},
        'document': {'$ref': get_ref_for_pid('doc', document.pid)},
        'quantity': 3,
        'amount': 15
    }
    order_line_4 = _make_resource(client, 'acol', data)
    order_line_4_ref = get_ref_for_pid('acol', order_line_4.pid)
    assert order_line_4.get('total_amount') == 45
    assert order_line_4.quantity == 3
    assert order_line_4.received_quantity == 0
    assert order_line_4.unreceived_quantity == 3
    assert not order_line_4.is_cancelled
    assert order_line_4.status == AcqOrderLineStatus.APPROVED

    data = {
        'acq_account': {'$ref': get_ref_for_pid('acac', m_serials_acc.pid)},
        'acq_order': {'$ref': get_ref_for_pid('acor', order.pid)},
        'document': {'$ref': get_ref_for_pid('doc', document.pid)},
        'quantity': 1,
        'amount': 150
    }
    order_line_5 = _make_resource(client, 'acol', data)
    order_line_5_ref = get_ref_for_pid('acol', order_line_5.pid)
    assert order_line_5.get('total_amount') == 150
    assert order_line_5.quantity == 1
    assert order_line_5.received_quantity == 0
    assert order_line_5.unreceived_quantity == 1
    assert not order_line_5.is_cancelled
    assert order_line_5.status == AcqOrderLineStatus.APPROVED

    data = {
        'acq_account': {'$ref': get_ref_for_pid('acac', m_serials_acc.pid)},
        'acq_order': {'$ref': get_ref_for_pid('acor', order.pid)},
        'document': {'$ref': get_ref_for_pid('doc', document.pid)},
        'quantity': 10,
        'amount': 7
    }
    order_line_6 = _make_resource(client, 'acol', data)
    order_line_6_ref = get_ref_for_pid('acol', order_line_6.pid)
    assert order_line_6.get('total_amount') == 70
    assert order_line_6.quantity == 10
    assert order_line_6.received_quantity == 0
    assert order_line_6.unreceived_quantity == 10
    assert not order_line_6.is_cancelled
    assert order_line_6.status == AcqOrderLineStatus.APPROVED

    # test order after adding lines
    assert order.get_order_provisional_total_amount() == 715
    assert order.status == AcqOrderStatus.PENDING
    # TODO: fix links to me for the order resource, this should fail
    assert order.can_delete
    assert not order.order_date
    assert order.item_quantity == 24
    assert order.item_received_quantity == 0

    manual_controls = {
        m_root_acc: ((5000, 9285), (0, 0), (0, 715)),
        m_books_acc: ((1550, 1550), (0, 0), (450, 0)),
        m_serials_acc: ((2735, 2735), (0, 0), (265, 0)),
        s_root_acc: ((13500, 20000), (0, 0), (0, 0)),
        s_books_acc: ((2500, 2500), (0, 0), (0, 0)),
        s_serials_acc: ((4000, 4000), (0, 0), (0, 0))
    }
    assert_account_data(manual_controls)

    # STEP 3 :: UPDATE ORDER LINES
    #   * Cancel some order lines and change some quantities --> make sure
    #     calculations still good
    #       martigny_books_account:
    #           line_1: quantity: 5 of amount 10   = 50
    #           line_2: quantity: 6 of amount 50   = 300  (quantity: 2 --> 6)
    #           line_3: quantity: 3 of amount 100  = 300 but cancelled !
    #                                        Total = 350
    #       martigny_serials_account:
    #           line_1: quantity: 3 of amount 15   = 45
    #           line_2: quantity: 2 of amount 150  = 300  (quantity: 1 --> 2)
    #           line_3: quantity: 10 of amount 7   = 70  but cancelled
    #                                        Total = 345
    #       Items quantity = 16: order total amount = 695

    order_line_2['quantity'] = 6
    order_line_2.update(order_line_2, dbcommit=True, reindex=True)
    order_line_3['is_cancelled'] = True
    order_line_3.update(order_line_3, dbcommit=True, reindex=True)
    order_line_5['quantity'] = 2
    order_line_5.update(order_line_5, dbcommit=True, reindex=True)
    order_line_6['is_cancelled'] = True
    order_line_6.update(order_line_6, dbcommit=True, reindex=True)

    # ensure correct calculations and status again
    manual_controls = {
        m_root_acc: ((5000, 9305), (0, 0), (0, 695)),
        m_books_acc: ((1650, 1650), (0, 0), (350, 0)),
        m_serials_acc: ((2655, 2655), (0, 0), (345, 0)),
        s_root_acc: ((13500, 20000), (0, 0), (0, 0)),
        s_books_acc: ((2500, 2500), (0, 0), (0, 0)),
        s_serials_acc: ((4000, 4000), (0, 0), (0, 0))
    }
    assert_account_data(manual_controls)

    assert order_line_6.get('total_amount') == 70
    assert order_line_6.is_cancelled
    assert order_line_6.quantity == 10
    assert order_line_6.received_quantity == 0
    assert order_line_6.unreceived_quantity == 10
    assert order_line_6.status == AcqOrderLineStatus.CANCELLED

    assert order_line_5.get('total_amount') == 300
    assert not order_line_5.is_cancelled
    assert order_line_5.quantity == 2
    assert order_line_5.received_quantity == 0
    assert order_line_5.unreceived_quantity == 2
    assert order_line_5.status == AcqOrderLineStatus.APPROVED

    assert order_line_4.get('total_amount') == 45
    assert not order_line_4.is_cancelled
    assert order_line_4.quantity == 3
    assert order_line_4.received_quantity == 0
    assert order_line_4.unreceived_quantity == 3
    assert order_line_4.status == AcqOrderLineStatus.APPROVED

    assert order_line_3.get('total_amount') == 300
    assert order_line_3.is_cancelled
    assert order_line_3.quantity == 3
    assert order_line_3.received_quantity == 0
    assert order_line_3.unreceived_quantity == 3
    assert order_line_3.status == AcqOrderLineStatus.CANCELLED

    assert order_line_2.get('total_amount') == 300
    assert not order_line_2.is_cancelled
    assert order_line_2.quantity == 6
    assert order_line_2.received_quantity == 0
    assert order_line_2.unreceived_quantity == 6
    assert order_line_2.status == AcqOrderLineStatus.APPROVED

    assert order_line_1.get('total_amount') == 50
    assert not order_line_1.is_cancelled
    assert order_line_1.quantity == 5
    assert order_line_1.received_quantity == 0
    assert order_line_1.unreceived_quantity == 5
    assert order_line_1.status == AcqOrderLineStatus.APPROVED

    # STEP 4 :: SEND THE ORDER
    #    * Test send order and make sure statuses are up to date.
    #      - check order lines (status, order-date)
    #      - check order (status)
    #      - check notification
    address = vendor_martigny\
        .get_contact(VendorContactType.DEFAULT)\
        .get('email')
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
    assert res.status_code == 200

    for order_line in [
        {'line': order_line_1, 'status': AcqOrderLineStatus.ORDERED},
        {'line': order_line_2, 'status': AcqOrderLineStatus.ORDERED},
        {'line': order_line_3, 'status': AcqOrderLineStatus.CANCELLED},
        {'line': order_line_4, 'status': AcqOrderLineStatus.ORDERED},
        {'line': order_line_5, 'status': AcqOrderLineStatus.ORDERED},
        {'line': order_line_6, 'status': AcqOrderLineStatus.CANCELLED},
    ]:
        line = AcqOrderLine.get_record_by_pid(order_line.get('line').pid)
        assert line.status == order_line.get('status')
        if line.status == AcqOrderLineStatus.CANCELLED:
            assert not line.order_date
        else:
            assert line.order_date
    # check order
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

    # STEP 5 :: CREATE A RECEIPT
    #   * create a receipt without any order lines yet
    #   * but with some adjustments
    ref_acc_book = get_ref_for_pid('acac', m_books_acc.pid)
    ref_acc_serial = get_ref_for_pid('acac', m_serials_acc.pid)
    data = {
        'acq_order': {'$ref': get_ref_for_pid('acor', order.pid)},
        'exchange_rate': 1,
        'amount_adjustments': [
            {
                'label': 'handling fees',
                'amount': 2.0,
                'acq_account': {'$ref': ref_acc_book}
            },
            {
                'label': 'discount',
                'amount': -1.0,
                'acq_account': {'$ref': ref_acc_book}
            },
            {
                'label': 'handling fees',
                'amount': 10,
                'acq_account': {'$ref': ref_acc_serial}
            }
        ],
        'library': {'$ref': get_ref_for_pid('lib', lib_martigny.pid)},
        'organisation': {'$ref': get_ref_for_pid('org', org_martigny.pid)}
    }
    receipt_1 = _make_resource(client, 'acre', data)
    assert receipt_1.total_amount == 11  # 2 - 1 + 10
    assert receipt_1.can_delete

    manual_controls = {
        m_root_acc: ((5000, 9294), (0, 11), (0, 695)),
        m_books_acc: ((1649, 1649), (1, 0), (350, 0)),
        m_serials_acc: ((2645, 2645), (10, 0), (345, 0)),
        s_root_acc: ((13500, 20000), (0, 0), (0, 0)),
        s_books_acc: ((2500, 2500), (0, 0), (0, 0)),
        s_serials_acc: ((4000, 4000), (0, 0), (0, 0))
    }
    assert_account_data(manual_controls)

    # STEP 6 :: RECEIVE SOME ORDER LINES
    #    Received 2 items from the order_line_1. We need to ensure :
    #    * the order_line status is PARTIALLY_RECEIVED
    #    * the order status is PARTIALLY_RECEIVED too
    #    * the related account amounts are correctly assigned

    # CHECK :: Not possible to receive quantity more than what you ordered
    res, data = postdata(
        client,
        'api_receipt.lines',
        data=[{
            'acq_order_line': {'$ref': order_line_1_ref},
            'amount': 10,
            'quantity': 12,
            'receipt_date': '2021-11-01'
        }],
        url_data=dict(receipt_pid=receipt_1.pid)
    )
    assert res.status_code == 200
    response = data.get('response')
    assert response[0]['status'] == AcqReceiptLineCreationStatus.FAILURE

    # partially receive one order with few quantities in receipt_1
    res, data = postdata(
        client,
        'api_receipt.lines',
        data=[{
            'acq_order_line': {'$ref': order_line_1_ref},
            'amount': 10,
            'quantity': 2,
            'vat_rate': 6,
            'receipt_date': '2021-11-01'
        }],
        url_data=dict(receipt_pid=receipt_1.pid)
    )
    assert res.status_code == 200
    response = data.get('response')
    assert response[0]['status'] == AcqReceiptLineCreationStatus.SUCCESS

    # Test order and order lines
    for order_line in [{
        'line': order_line_1,
        'status': AcqOrderLineStatus.PARTIALLY_RECEIVED,
        'received': 2
    }, {
        'line': order_line_2,
        'status': AcqOrderLineStatus.ORDERED,
        'received': 0
    }, {
        'line': order_line_3,
        'status': AcqOrderLineStatus.CANCELLED,
        'received': 0
    }, {
        'line': order_line_4,
        'status': AcqOrderLineStatus.ORDERED,
        'received': 0
    }, {
        'line': order_line_5,
        'status': AcqOrderLineStatus.ORDERED,
        'received': 0
    }, {
        'line': order_line_6,
        'status': AcqOrderLineStatus.CANCELLED,
        'received': 0
    }]:
        line = AcqOrderLine.get_record_by_pid(order_line.get('line').pid)
        assert line.status == order_line.get('status')
        assert line.received_quantity == order_line.get('received')
    order = AcqOrder.get_record_by_pid(order.pid)
    assert order.status == AcqOrderStatus.PARTIALLY_RECEIVED

    manual_controls = {
        m_root_acc: ((5000, 9292.8), (0, 32.2), (0, 675)),
        m_books_acc: ((1647.8, 1647.8), (22.2, 0), (330, 0)),
        m_serials_acc: ((2645, 2645), (10, 0), (345, 0)),
        s_root_acc: ((13500, 20000), (0, 0), (0, 0)),
        s_books_acc: ((2500, 2500), (0, 0), (0, 0)),
        s_serials_acc: ((4000, 4000), (0, 0), (0, 0))
    }
    assert_account_data(manual_controls)

    # STEP 7 :: CREATE NEW RECEIVE AND RECEIVE ALL PENDING ORDER LINES
    #   * Create a second receipt for the same order with no adjustments.
    #   * To to receive all pending order lines BUT with a mistake for
    #     `order_line_5` (try to receive more than ordered items) ==> all lines
    #     except `order_line_5` should have the RECEIVED STATUS
    #   * complete the order reception to receive the `order_line_5`
    data = {
        'exchange_rate': 1,
        'acq_order': {'$ref': get_ref_for_pid('acor', order.pid)},
        'library': {'$ref': get_ref_for_pid('lib', lib_martigny.pid)},
        'organisation': {'$ref': get_ref_for_pid('org', org_martigny.pid)}
    }
    receipt_2 = _make_resource(client, 'acre', data)

    data = [{
        'acq_order_line': {'$ref': order_line_1_ref},
        'amount': 10,
        'quantity': 3,
        'receipt_date': '2021-11-01'
    }, {
        'acq_order_line': {'$ref': order_line_2_ref},
        'amount': 50,
        'quantity': 6,
        'receipt_date': '2021-11-01'
    }, {
        'acq_order_line': {'$ref': order_line_4_ref},
        'amount': 15,
        'quantity': 3,
        'receipt_date': '2021-11-01'
    }, {
        'acq_order_line': {'$ref': order_line_5_ref},
        'amount': 150,
        'quantity': 12,  # too many items ! Max quantity should be 2
        'receipt_date': '2021-11-01'
    }]
    res, data = postdata(
        client,
        'api_receipt.lines',
        data=data,
        url_data=dict(receipt_pid=receipt_2.pid)
    )

    assert res.status_code == 200
    response = data.get('response')
    assert response[0]['status'] == AcqReceiptLineCreationStatus.SUCCESS
    assert response[1]['status'] == AcqReceiptLineCreationStatus.SUCCESS
    assert response[2]['status'] == AcqReceiptLineCreationStatus.SUCCESS
    assert response[3]['status'] == AcqReceiptLineCreationStatus.FAILURE

    # Test order and order lines
    for order_line in [
        {'line': order_line_1, 'status': AcqOrderLineStatus.RECEIVED},
        {'line': order_line_2, 'status': AcqOrderLineStatus.RECEIVED},
        {'line': order_line_3, 'status': AcqOrderLineStatus.CANCELLED},
        {'line': order_line_4, 'status': AcqOrderLineStatus.RECEIVED},
        {'line': order_line_5, 'status': AcqOrderLineStatus.ORDERED},
        {'line': order_line_6, 'status': AcqOrderLineStatus.CANCELLED}
    ]:
        line = AcqOrderLine.get_record_by_pid(order_line.get('line').pid)
        assert line.status == order_line.get('status')

    # Receive the last pending order_line
    data = [{
        'acq_order_line': {'$ref': order_line_5_ref},
        'amount': 150,
        'quantity': 2,
        'receipt_date': '2021-11-01'
    }]
    res, data = postdata(
        client,
        'api_receipt.lines',
        data=data,
        url_data=dict(receipt_pid=receipt_2.pid)
    )
    assert res.status_code == 200
    response = data.get('response')
    assert response[0]['status'] == AcqReceiptLineCreationStatus.SUCCESS
    order_line = AcqOrderLine.get_record_by_pid(order_line_5.pid)
    assert order_line.status == AcqOrderLineStatus.RECEIVED

    # check than order is now fully received
    order = AcqOrder.get_record_by_pid(order.pid)
    assert order.status == AcqOrderStatus.RECEIVED
    # check account amounts
    manual_controls = {
        m_root_acc: ((5000, 9292.8), (0, 707.2), (0, 0)),
        m_books_acc: ((1647.8, 1647.8), (352.2, 0), (0, 0)),
        m_serials_acc: ((2645, 2645), (355, 0), (0, 0)),
        s_root_acc: ((13500, 20000), (0, 0), (0, 0)),
        s_books_acc: ((2500, 2500), (0, 0), (0, 0)),
        s_serials_acc: ((4000, 4000), (0, 0), (0, 0))
    }
    assert_account_data(manual_controls)

    # TEST 8: DELETE RECEIPTS
    #   * Delete the second receipt. This will also delete the related receipt
    #     lines. The order status must remain to PARTIALLY_RECEIVED.
    #   * Delete the first receipt. The order status should remain to ORDERED
    #     and account amount should be the same than STEP#3.

    # Check links between object
    #   * check some order lines (cancelled or not); not need to test all lines
    #   * check receipt links
    links = order.get_links_to_me(get_pids=True)
    for pid in [order_line_3.pid, order_line_4.pid, order_line_5.pid]:
        assert pid in links['order_lines']
    for pid in [receipt_1.pid, receipt_2.pid]:
        assert pid in links['receipts']

    # DELETE `RECEIPT_2` ----------
    receipt_line_pids = receipt_2.get_receipt_lines(output='pids')
    url = url_for('invenio_records_rest.acre_item', pid_value=receipt_2.pid)
    client.delete(url)
    # Check all resources related to `receipt_2` is deleted
    for pid in receipt_line_pids:
        line = AcqReceiptLine.get_record_by_pid(pid)
        assert line is None
    assert AcqReceipt.get_record_by_pid(receipt_2.pid) is None
    # Check ES is up-to-date
    response = AcqReceiptLinesSearch()\
        .filter('terms', pid=receipt_line_pids).execute()
    assert response.hits.total.value == 0
    response = AcqReceiptsSearch() \
        .filter('term', pid=receipt_2.pid).execute()
    assert response.hits.total.value == 0
    # Check order status
    order = AcqOrder.get_record_by_pid(order.pid)
    assert order.status == AcqOrderStatus.PARTIALLY_RECEIVED

    # DELETE `RECEIPT_1` ----------
    receipt_line_pids = receipt_1.get_receipt_lines(output='pids')
    url = url_for('invenio_records_rest.acre_item', pid_value=receipt_1.pid)
    client.delete(url)
    # Check all resources related to `receipt_1` is deleted
    for pid in receipt_line_pids:
        line = AcqReceiptLine.get_record_by_pid(pid)
        assert line is None
    assert AcqReceipt.get_record_by_pid(receipt_1.pid) is None
    # Check ES is up-to-date
    response = AcqReceiptLinesSearch() \
        .filter('terms', pid=receipt_line_pids).execute()
    assert response.hits.total.value == 0
    response = AcqReceiptsSearch() \
        .filter('term', pid=receipt_1.pid).execute()
    assert response.hits.total.value == 0
    # Check order status
    order = AcqOrder.get_record_by_pid(order.pid)
    assert order.status == AcqOrderStatus.ORDERED

    # ensure correct calculations and status again
    manual_controls = {
        m_root_acc: ((5000, 9305), (0, 0), (0, 695)),
        m_books_acc: ((1650, 1650), (0, 0), (350, 0)),
        m_serials_acc: ((2655, 2655), (0, 0), (345, 0)),
        s_root_acc: ((13500, 20000), (0, 0), (0, 0)),
        s_books_acc: ((2500, 2500), (0, 0), (0, 0)),
        s_serials_acc: ((4000, 4000), (0, 0), (0, 0))
    }
    assert_account_data(manual_controls)
