# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2020 RERO
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

from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import get_json


def test_local_fields_permissions_api(
        client, org_martigny, document, local_field_martigny,
        patron_sion, librarian_martigny):
    """Test local fields permissions api."""
    local_field_permissions_url = url_for(
        'api_blueprint.permissions',
        route_name='local_fields'
    )
    local_field_martigny_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='local_fields',
        record_pid=local_field_martigny.pid
    )

    # Not logged
    res = client.get(local_field_permissions_url)
    assert res.status_code == 401

    # Logged as patron
    login_user_via_session(client, patron_sion.user)
    res = client.get(local_field_permissions_url)
    assert res.status_code == 403

    # Logged as
    login_user_via_session(client, librarian_martigny.user)
    res = client.get(local_field_martigny_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['create']['can']
    assert data['delete']['can']
    assert data['list']['can']
    assert data['read']['can']
    assert data['update']['can']
