# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
# Copyright (C) 2021 UCLouvain
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

"""Test acquisition order API."""
import mock
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import get_json, postdata

from rero_ils.modules.acq_order_lines.api import AcqOrderLine
from rero_ils.modules.acq_order_lines.models import AcqOrderLineStatus
from rero_ils.modules.acq_orders.api import AcqOrder
from rero_ils.modules.acq_orders.models import AcqOrderStatus
from rero_ils.modules.notifications.api import Notification
from rero_ils.modules.notifications.models import NotificationChannel, \
    NotificationStatus, NotificationType, RecipientType


def test_order_notification_preview(
    app, client, librarian_martigny,
    acq_order_fiction_martigny,
    acq_order_line_fiction_martigny,
    acq_order_line2_fiction_martigny
):
    """Test order notification preview API."""
    login_user_via_session(client, librarian_martigny.user)
    acor = acq_order_fiction_martigny

    url = url_for('api_order.order_notification_preview', order_pid=acor.pid)
    res = client.get(url)
    assert res.status_code == 200
    data = get_json(res)
    assert 'data' in data and 'preview' in data
    assert 'message' not in data

    # update the vendor communication_language to force it to an unknown
    # related template and retry.
    mocked_data = data['data']
    mocked_data['vendor']['language'] = 'dummy'
    magic_mock = mock.MagicMock(return_value=mocked_data)
    with mock.patch(
        'rero_ils.modules.acq_orders.api.AcqOrder.dumps',
        magic_mock
    ):
        res = client.get(url)
        assert res.status_code == 200
        data = get_json(res)
        assert 'data' in data and 'preview' in data and 'message' in data


def test_send_order(
    app, client, librarian_martigny, lib_martigny,
    acq_order_fiction_martigny,
    acq_order_line_fiction_martigny, vendor_martigny,
    acq_order_line2_fiction_martigny, acq_order_line3_fiction_martigny
):
    """Test send order notification API."""
    login_user_via_session(client, librarian_martigny.user)
    acor = acq_order_fiction_martigny
    address = vendor_martigny.get('default_contact').get('email')
    emails = [{'type': 'cc', 'address': address}]
    # test when parent order is not in database
    res, data = postdata(
        client,
        'api_order.send_order',
        data=dict(emails=emails),
        url_data=dict(order_pid='toto')
    )
    assert res.status_code == 404
    # test when email data is not provided
    res, data = postdata(
        client,
        'api_order.send_order',
        url_data=dict(order_pid=acor.pid)
    )
    assert res.status_code == 400
    # test when email data provided but empty
    res, data = postdata(
        client,
        'api_order.send_order',
        data=dict(emails=[]),
        url_data=dict(order_pid=acor.pid)
    )
    assert res.status_code == 400
    # test when email data provided and has no "to" email address
    res, data = postdata(
        client,
        'api_order.send_order',
        data=dict(emails=emails),
        url_data=dict(order_pid=acor.pid)
    )
    assert res.status_code == 400
    assert 'required' in data['message'] and '`to`' in data['message']
    # have an order line with a status different than approved and ensure it
    # will not be ordered
    l3 = AcqOrderLine.get_record_by_pid(acq_order_line3_fiction_martigny.pid)
    l3['status'] = AcqOrderLineStatus.CANCELLED
    l3.update(l3, dbcommit=True, reindex=True)

    # test send order with correct input parameters
    emails = [
        {'type': 'to', 'address': address},
        {'type': 'reply_to', 'address': lib_martigny.get('email')}
    ]
    res, data = postdata(
        client,
        'api_order.send_order',
        data=dict(emails=emails),
        url_data=dict(order_pid=acor.pid)
    )
    assert res.status_code == 200
    data = get_json(res)
    acor = AcqOrder.get_record_by_pid(acor.pid)
    l1 = AcqOrderLine.get_record_by_pid(acq_order_line_fiction_martigny.pid)
    l2 = AcqOrderLine.get_record_by_pid(acq_order_line2_fiction_martigny.pid)
    l3 = AcqOrderLine.get_record_by_pid(acq_order_line3_fiction_martigny.pid)
    # Approved order lines are ordered
    assert l1.get('status') == AcqOrderLineStatus.ORDERED
    assert l2.get('status') == AcqOrderLineStatus.ORDERED
    # Cancelled order lines remain cancelled (not ordered)
    assert l3.get('status') == AcqOrderLineStatus.CANCELLED
    assert acor.status == AcqOrderStatus.ORDERED
    # ensure that created notification is well constructed from the associated
    # order and vendor
    notification_pid = data.get('data').get('pid')
    notif = Notification.get_record_by_pid(notification_pid)
    assert notif.organisation_pid == acor.organisation_pid
    assert notif.aggregation_key == str(notif.id)
    assert notif.type == NotificationType.ACQUISITION_ORDER
    assert notif.status == NotificationStatus.DONE
    assert notif.acq_order_pid == acor.pid
    assert notif.library_pid == acor.library_pid
    assert notif.can_be_cancelled() == (False, None)
    assert notif.get_communication_channel() == NotificationChannel.EMAIL
    assert notif.get_language_to_use() == \
        vendor_martigny.get('communication_language')
    assert address in notif.get_recipients(RecipientType.TO)
