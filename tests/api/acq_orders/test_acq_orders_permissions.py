# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2022 RERO
# Copyright (C) 2022 UCLouvain
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

from rero_ils.modules.acq_orders.permissions import AcqOrderPermission


def test_orders_permissions_api(client, org_martigny, vendor2_martigny,
                                patron_martigny,
                                system_librarian_martigny,
                                librarian_martigny,
                                acq_order_fiction_saxon,
                                acq_order_fiction_martigny,
                                acq_order_fiction_sion):
    """Test orders permissions api."""
    acq_order_permissions_url = url_for(
        'api_blueprint.permissions',
        route_name='acq_orders'
    )
    acq_order_martigny_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='acq_orders',
        record_pid=acq_order_fiction_martigny.pid
    )
    acq_order_saxon_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='acq_orders',
        record_pid=acq_order_fiction_saxon.pid
    )
    acq_order_sion_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='acq_orders',
        record_pid=acq_order_fiction_sion.pid
    )

    # Not logged
    res = client.get(acq_order_permissions_url)
    assert res.status_code == 401

    # Logged as patron
    login_user_via_session(client, patron_martigny.user)
    res = client.get(acq_order_permissions_url)
    assert res.status_code == 403

    # Logged as librarian
    #   * lib can 'list' and 'read' orders of its own organisation
    #   * lib can 'create', 'update', delete only for its library
    #   * lib can't 'read' acq_account of others organisation.
    #   * lib can't 'create', 'update', 'delete' orders for other org/lib
    login_user_via_session(client, librarian_martigny.user)
    res = client.get(acq_order_martigny_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert data['create']['can']
    assert data['update']['can']
    assert data['delete']['can']

    res = client.get(acq_order_saxon_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert not data['read']['can']
    assert data['list']['can']
    assert not data['update']['can']
    assert not data['delete']['can']

    res = client.get(acq_order_sion_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert not data['read']['can']
    assert data['list']['can']
    assert not data['update']['can']
    assert not data['delete']['can']

    # Logged as system librarian
    #   * sys_lib can do everything about orders of its own organisation
    #   * sys_lib can't do anything about orders of other organisation
    login_user_via_session(client, system_librarian_martigny.user)
    res = client.get(acq_order_saxon_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert data['create']['can']
    assert data['update']['can']
    assert data['delete']['can']

    res = client.get(acq_order_sion_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert not data['read']['can']
    assert not data['update']['can']
    assert not data['delete']['can']


def test_orders_permissions(patron_martigny,
                            librarian_martigny,
                            system_librarian_martigny,
                            org_martigny, vendor2_martigny,
                            acq_order_fiction_sion,
                            acq_order_fiction_saxon,
                            acq_order_fiction_martigny):
    """Test orders permissions class."""

    # Anonymous user
    assert not AcqOrderPermission.list(None, {})
    assert not AcqOrderPermission.read(None, {})
    assert not AcqOrderPermission.create(None, {})
    assert not AcqOrderPermission.update(None, {})
    assert not AcqOrderPermission.delete(None, {})

    # As non Librarian
    acq_order_martigny = acq_order_fiction_martigny
    acq_order_saxon = acq_order_fiction_saxon
    acq_order_sion = acq_order_fiction_sion
    assert not AcqOrderPermission.list(None, acq_order_martigny)
    assert not AcqOrderPermission.read(None, acq_order_martigny)
    assert not AcqOrderPermission.create(None, acq_order_martigny)
    assert not AcqOrderPermission.update(None, acq_order_martigny)
    assert not AcqOrderPermission.delete(None, acq_order_martigny)

    # As Librarian
    with mock.patch(
        'rero_ils.modules.permissions.current_librarian',
        librarian_martigny
    ):
        assert AcqOrderPermission.list(None, acq_order_martigny)
        assert AcqOrderPermission.read(None, acq_order_martigny)
        assert AcqOrderPermission.create(None, acq_order_martigny)
        assert AcqOrderPermission.update(None, acq_order_martigny)
        assert AcqOrderPermission.delete(None, acq_order_martigny)

        assert not AcqOrderPermission.read(None, acq_order_saxon)
        assert not AcqOrderPermission.create(None, acq_order_saxon)
        assert not AcqOrderPermission.update(None, acq_order_saxon)
        assert not AcqOrderPermission.delete(None, acq_order_saxon)

        assert not AcqOrderPermission.read(None, acq_order_sion)
        assert not AcqOrderPermission.create(None, acq_order_sion)
        assert not AcqOrderPermission.update(None, acq_order_sion)
        assert not AcqOrderPermission.delete(None, acq_order_sion)

    # As System-librarian
    with mock.patch(
        'rero_ils.modules.permissions.current_librarian',
        system_librarian_martigny
    ):
        assert AcqOrderPermission.list(None, acq_order_saxon)
        assert AcqOrderPermission.read(None, acq_order_saxon)
        assert AcqOrderPermission.create(None, acq_order_saxon)
        assert AcqOrderPermission.update(None, acq_order_saxon)
        assert AcqOrderPermission.delete(None, acq_order_saxon)

        assert not AcqOrderPermission.read(None, acq_order_sion)
        assert not AcqOrderPermission.create(None, acq_order_sion)
        assert not AcqOrderPermission.update(None, acq_order_sion)
        assert not AcqOrderPermission.delete(None, acq_order_sion)
