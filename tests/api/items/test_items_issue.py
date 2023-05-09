# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
# Copyright (C) 2019-2023 UCLouvain
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

import mock
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import VerifyRecordPermissionPatch, flush_index, get_csv, \
    get_json, parse_csv, postdata

from rero_ils.modules.holdings.api import Holding
from rero_ils.modules.items.api import Item
from rero_ils.modules.notifications.api import Notification, \
    NotificationsSearch
from rero_ils.modules.notifications.models import NotificationType, \
    RecipientType
from rero_ils.modules.notifications.tasks import process_notifications
from rero_ils.modules.utils import get_ref_for_pid


def _receive_regular_issue(client, holding):
    res, data = postdata(
        client,
        'api_holding.receive_regular_issue',
        url_data=dict(holding_pid=holding.pid)
    )
    assert res.status_code == 200
    data = get_json(res)
    issue_item = Item.get_record_by_pid(data.get('issue', {}).get('pid'))
    assert issue_item is not None
    assert issue_item.issue_is_regular
    return issue_item


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_issues_permissions(
    client, holding_lib_martigny_w_patterns, librarian_martigny
):
    """Test specific items issues permissions."""

    # receive a regular issue
    holding = holding_lib_martigny_w_patterns
    holding = Holding.get_record_by_pid(holding.pid)
    login_user_via_session(client, librarian_martigny.user)
    issue_item = _receive_regular_issue(client, holding)

    res = client.get(
        url_for(
            'api_blueprint.permissions',
            route_name='items',
            record_pid=issue_item.pid
        )
    )
    assert res.status_code == 200
    data = get_json(res)
    assert data['delete']['can']


def test_issues_claim_notifications(
    client, holding_lib_martigny_w_patterns, librarian_martigny, mailbox,
    csv_header
):
    """Test claim notification creation."""
    mailbox.clear()

    # receive a regular issue
    holding = holding_lib_martigny_w_patterns
    holding = Holding.get_record_by_pid(holding.pid)
    login_user_via_session(client, librarian_martigny.user)
    issue_item = _receive_regular_issue(client, holding)
    # Ensure than no claim already exists about this new issue
    assert issue_item.claims_count == 0

    # Create a claim notification for this issue item and dispatch it
    # TODO :: In next PR :
    #   - 1) call claim notification preview
    #   - 2) call API to create claim notification (with recipients in JSON)
    #   - 3) dispatch the notification
    notif_data = {
        'notification_type': NotificationType.CLAIM_ISSUE,
        'context': {
            'item': {'$ref': get_ref_for_pid(Item, issue_item.pid)},
            'recipients': [
                {'type': RecipientType.TO, 'address': 'test@domain.com'},
                {'type': RecipientType.CC, 'address': 'test_cc@domain.com'},
                {'type': RecipientType.REPLY_TO, 'address': 'reply@to.com'}
            ],
            'number': 0,
        }
    }
    notification = Notification.create(notif_data, dbcommit=True, reindex=True)
    flush_index(NotificationsSearch.Meta.index)
    assert notification
    process_notifications(NotificationType.CLAIM_ISSUE)
    assert len(mailbox) == 1

    # As a claim notification has been created, the number of claim for this
    # issue should be incremented
    flush_index(NotificationsSearch.Meta.index)
    assert issue_item.claims_count == 1

    # Export this issue as CSV and check issue claims_count column
    list_url = url_for('api_item.inventory_search', q=f'pid:{issue_item.pid}')
    response = client.get(list_url, headers=csv_header)
    assert response.status_code == 200
    data = list(parse_csv(get_csv(response)))
    assert len(data) == 2  # header + 1 row
    assert data[1][-8] == str(1)  # same as `issue_item.claims_count`
