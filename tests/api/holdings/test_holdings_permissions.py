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
from invenio_accounts.testutils import login_user_via_session
from utils import get_json

from rero_ils.modules.holdings.permissions import HoldingPermission


def test_holdings_permissions_api(client, patron_martigny,
                                  system_librarian_martigny,
                                  librarian_martigny,
                                  holding_lib_martigny, holding_lib_saxon,
                                  holding_lib_sion,
                                  holding_lib_martigny_w_patterns):
    """Test holdings permissions api."""
    holding_permissions_url = url_for(
        'api_blueprint.permissions',
        route_name='holdings'
    )
    holding_martigny_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='holdings',
        record_pid=holding_lib_martigny.pid
    )
    holding_serial_martigny_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='holdings',
        record_pid=holding_lib_martigny_w_patterns.pid
    )
    holding_saxon_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='holdings',
        record_pid=holding_lib_saxon.pid
    )
    holding_sion_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='holdings',
        record_pid=holding_lib_saxon.pid
    )

    # Not logged
    res = client.get(holding_permissions_url)
    assert res.status_code == 401

    # Logged as patron
    login_user_via_session(client, patron_martigny.user)
    res = client.get(holding_permissions_url)
    assert res.status_code == 403

    # Logged as librarian
    #   * lib can 'list' and 'read' holding of its own organisation
    #   * lib can 'create', 'update', 'delete' only for its own organisation
    #   * lib can't 'create', 'update', 'delete' item for other organisation
    login_user_via_session(client, librarian_martigny.user)
    res = client.get(holding_martigny_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert data['create']['can']
    assert not data['update']['can']
    assert not data['delete']['can']

    res = client.get(holding_serial_martigny_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert data['create']['can']
    assert data['update']['can']
    assert data['delete']['can']

    res = client.get(holding_saxon_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert not data['update']['can']
    assert not data['delete']['can']

    res = client.get(holding_sion_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert not data['update']['can']
    assert not data['delete']['can']

    # Logged as system librarian
    #   * sys_lib can do everything about patron of its own organisation
    #   * sys_lib can't do anything about patron of other organisation
    login_user_via_session(client, system_librarian_martigny.user)
    res = client.get(holding_saxon_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert data['create']['can']
    assert not data['update']['can']
    assert not data['delete']['can']

    res = client.get(holding_serial_martigny_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert data['create']['can']
    assert data['update']['can']
    assert data['delete']['can']

    res = client.get(holding_sion_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert not data['update']['can']
    assert not data['delete']['can']


def test_holdings_permissions(patron_martigny, org_martigny,
                              librarian_martigny,
                              system_librarian_martigny,
                              holding_lib_sion, holding_lib_saxon,
                              holding_lib_martigny,
                              holding_lib_martigny_w_patterns,
                              holding_lib_sion_w_patterns):
    """Test holdings permissions class."""

    # Anonymous user
    assert HoldingPermission.list(None, {})
    assert HoldingPermission.read(None, {})
    assert not HoldingPermission.create(None, {})
    assert not HoldingPermission.update(None, {})
    assert not HoldingPermission.delete(None, {})

    # As non Librarian
    holding_serial_martigny = holding_lib_martigny_w_patterns
    holding_serial_sion = holding_lib_sion_w_patterns
    assert HoldingPermission.list(None, holding_lib_martigny)
    assert HoldingPermission.read(None, holding_lib_martigny)
    assert not HoldingPermission.create(None, holding_lib_martigny)
    assert not HoldingPermission.update(None, holding_lib_martigny)
    assert not HoldingPermission.delete(None, holding_lib_martigny)

    # As Librarian
    with mock.patch(
        'rero_ils.modules.holdings.permissions.current_librarian',
        librarian_martigny
    ):
        assert HoldingPermission.list(None, holding_lib_martigny)
        assert HoldingPermission.read(None, holding_lib_martigny)
        assert not HoldingPermission.create(None, holding_lib_martigny)
        assert not HoldingPermission.update(None, holding_lib_martigny)
        assert not HoldingPermission.delete(None, holding_lib_martigny)

        assert HoldingPermission.create(None, holding_serial_martigny)
        assert HoldingPermission.update(None, holding_serial_martigny)
        assert HoldingPermission.delete(None, holding_serial_martigny)

        assert HoldingPermission.read(None, holding_lib_saxon)
        assert not HoldingPermission.create(None, holding_lib_saxon)
        assert not HoldingPermission.update(None, holding_lib_saxon)
        assert not HoldingPermission.delete(None, holding_lib_saxon)

        assert HoldingPermission.read(None, holding_lib_sion)
        assert not HoldingPermission.create(None, holding_lib_sion)
        assert not HoldingPermission.update(None, holding_lib_sion)
        assert not HoldingPermission.delete(None, holding_lib_sion)

        assert not HoldingPermission.update(None, holding_serial_sion)
        assert not HoldingPermission.delete(None, holding_serial_sion)

    # As System-librarian
    with mock.patch(
        'rero_ils.modules.holdings.permissions.current_librarian',
        system_librarian_martigny
    ):
        assert HoldingPermission.list(None, HoldingPermission)
        assert HoldingPermission.read(None, HoldingPermission)
        assert HoldingPermission.create(None, holding_serial_martigny)
        assert HoldingPermission.update(None, holding_serial_martigny)
        assert HoldingPermission.delete(None, holding_serial_martigny)

        assert HoldingPermission.read(None, holding_lib_sion)
        assert not HoldingPermission.create(None, holding_lib_sion)
        assert not HoldingPermission.update(None, holding_lib_sion)
        assert not HoldingPermission.delete(None, holding_lib_sion)
