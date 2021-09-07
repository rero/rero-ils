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
from utils import get_json


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
