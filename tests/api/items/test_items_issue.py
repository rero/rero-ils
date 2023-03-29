# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2020 RERO
# Copyright (C) 2020 UCLouvain
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
from utils import VerifyRecordPermissionPatch, get_json, login_user, postdata

from rero_ils.modules.holdings.api import Holding
from rero_ils.modules.items.api import Item


@mock.patch('invenio_records_rest.views.verify_record_permission',
            mock.MagicMock(return_value=VerifyRecordPermissionPatch))
def test_issues_permissions(client, json_header,
                            holding_lib_martigny_w_patterns,
                            librarian_martigny):
    """Test specific items issues permissions."""

    # receive a regular issue
    holding = holding_lib_martigny_w_patterns
    holding = Holding.get_record_by_pid(holding.pid)
    login_user(client, librarian_martigny)
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
