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
from jinja2 import UndefinedError
from utils import VerifyRecordPermissionPatch, flush_index, get_csv, \
    get_json, parse_csv, postdata

from rero_ils.modules.commons.exceptions import MissingDataException
from rero_ils.modules.holdings.api import Holding
from rero_ils.modules.items.api import Item
from rero_ils.modules.items.dumpers import ClaimIssueNotificationDumper
from rero_ils.modules.notifications.api import Notification, \
    NotificationsSearch
from rero_ils.modules.notifications.models import RecipientType
from rero_ils.modules.vendors.dumpers import VendorClaimIssueNotificationDumper


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
    csv_header, rero_json_header, item_lib_sion
):
    """Test claim notification creation."""
    item = item_lib_sion
    mailbox.clear()

    # receive a regular issue
    holding = holding_lib_martigny_w_patterns
    holding = Holding.get_record_by_pid(holding.pid)
    login_user_via_session(client, librarian_martigny.user)
    issue_item = _receive_regular_issue(client, holding)
    # Ensure than no claim already exists about this new issue
    assert issue_item.claims_count == 0

    # Call the API to get the preview of the future claim notification.
    #   1) call with unknown item --> return 404
    #   2) call with a standard item --> return 400
    #   3) simulate a template rendering error --> return 500
    #   4) missing data --> return 500
    #   4) call with an issue item --> return 200
    for pid, ret_code in [('dummy_pid', 404), (item.pid, 400)]:
        url = url_for('api_item.claim_notification_preview', item_pid=pid)
        response = client.get(url)
        assert response.status_code == ret_code

    issue_pid = issue_item.pid
    url = url_for('api_item.claim_notification_preview', item_pid=issue_pid)
    with mock.patch('rero_ils.modules.items.views.api_views.render_template',
                    mock.MagicMock(side_effect=UndefinedError('my_error'))):
        response = client.get(url)
        assert response.status_code == 500
        assert 'my_error' in response.json['message']

    with mock.patch.object(
        ClaimIssueNotificationDumper, 'dump',
        mock.MagicMock(side_effect=MissingDataException('Test!'))
    ):
        response = client.get(url)
        assert response.status_code == 500
        assert 'Test!' in response.json['message']

    response = client.get(url)
    assert response.status_code == 200
    assert all(field in response.json
               for field in ['recipient_suggestions', 'preview'])
    assert 'message' not in response.json

    # update the vendor communication_language to force it to an unknown
    # related template and retry.
    with mock.patch.object(VendorClaimIssueNotificationDumper, 'dump',
                           mock.MagicMock(return_value={
                               'name': 'test vendor name',
                               'email': 'test@vendor.com',
                               'language': 'dummy'
                           })):
        response = client.get(url)
        assert response.status_code == 200
        assert all(
            field in response.json
            for field in ['recipient_suggestions', 'preview', 'message']
        )

    # Now really claim the issue
    #   1) sending bad item_pid --> return 4xx HTTP code
    #   2) not sending recipients data --> return 400 HTTP code
    #   3) sending all correct data : the notification is created, dispatched
    #      and returned
    for pid, ret_code in [('dummy_pid', 404), (item.pid, 400)]:
        url = url_for('api_item.claim_issue', item_pid=pid)
        response = client.post(url)
        assert response.status_code == ret_code

    response, data = postdata(
        client,
        'api_item.claim_issue',
        url_data={'item_pid': issue_pid},
        data={'recipients': []}
    )
    assert response.status_code == 400
    assert data['message'] == 'Missing recipients emails.'

    response, data = postdata(
        client,
        'api_item.claim_issue',
        url_data={'item_pid': issue_pid},
        data={'recipients': [
            {'type': RecipientType.TO, 'address': 'to@domain.com'},
            {'type': RecipientType.REPLY_TO, 'address': 'noreply@domain.com'},
            {'type': RecipientType.CC, 'address': 'cc1@domain.com'},
            {'type': RecipientType.CC, 'address': 'cc2@domain.com'},
            {'type': RecipientType.BCC, 'address': 'bcc@domain.com'},
        ]}
    )
    assert response.status_code == 200
    notification = Notification.get_record_by_pid(data['data']['pid'])
    assert notification
    assert len(mailbox) == 1
    assert notification['context']['number'] == 1

    # Send a second claims... just for fun (and also testing increment number)
    mailbox.clear()
    response, data = postdata(
        client,
        'api_item.claim_issue',
        url_data={'item_pid': issue_pid},
        data={'recipients': [
            {'type': RecipientType.TO, 'address': 'to2@domain.com'},
            {'type': RecipientType.REPLY_TO, 'address': 'noreply2@domain.com'}
        ]}
    )
    assert response.status_code == 200
    notification = Notification.get_record_by_pid(data['data']['pid'])
    assert notification
    assert len(mailbox) == 1
    assert notification['context']['number'] == 2

    # As a claim notification has been created, the number of claim for this
    # issue should be incremented
    flush_index(NotificationsSearch.Meta.index)
    assert issue_item.claims_count == 2

    # Check that all is correctly indexed into ES
    url = url_for(
        'invenio_records_rest.item_list',
        q=f'pid:{issue_pid}',
        facets='claims_date'
    )
    response = client.get(url)
    data = response.json['hits']['hits'][0]['metadata']
    assert data['issue']['claims']['counter'] == 2
    assert len(data['issue']['claims']['dates']) == 2

    # Ensure than item serialization includes claim keys
    url = url_for('invenio_records_rest.item_item', pid_value=issue_pid)
    response = client.get(url, headers=rero_json_header)
    assert response.json['metadata']['issue']['claims']['counter'] == 2
    assert len(response.json['metadata']['issue']['claims']['dates']) == 2

    # Export this issue as CSV and check issue claims_count column
    list_url = url_for('api_item.inventory_search', q=f'pid:{issue_pid}')
    response = client.get(list_url, headers=csv_header)
    assert response.status_code == 200
    data = list(parse_csv(get_csv(response)))
    assert len(data) == 2  # header + 1 row
    assert data[1][-8] == str(2)  # same as `issue_item.claims_count`
