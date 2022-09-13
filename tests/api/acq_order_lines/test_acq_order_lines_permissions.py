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

from rero_ils.modules.acquisition.acq_order_lines.permissions import \
    AcqOrderLinePermission


def test_order_lines_permissions_api(client, document, org_martigny,
                                     vendor2_martigny, lib_sion,
                                     patron_martigny,
                                     system_librarian_martigny,
                                     librarian_martigny,
                                     acq_order_line_fiction_martigny,
                                     acq_order_line_fiction_saxon,
                                     acq_order_line_fiction_sion):
    """Test order lines permissions api."""
    acq_oline_permissions_url = url_for(
        'api_blueprint.permissions',
        route_name='acq_order_lines'
    )
    acq_oline_martigny_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='acq_order_lines',
        record_pid=acq_order_line_fiction_martigny.pid
    )
    acq_oline_saxon_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='acq_order_lines',
        record_pid=acq_order_line_fiction_saxon.pid
    )
    acq_oline_sion_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='acq_order_lines',
        record_pid=acq_order_line_fiction_sion.pid
    )

    # Not logged
    res = client.get(acq_oline_permissions_url)
    assert res.status_code == 401

    # Logged as patron
    login_user_via_session(client, patron_martigny.user)
    res = client.get(acq_oline_permissions_url)
    assert res.status_code == 403

    # Logged as librarian
    #   * lib can 'list' and 'read' order lines of its own organisation
    #   * lib can 'create', 'update', delete only for its library
    #   * lib can't 'read' acq_account of others organisation.
    #   * lib can't 'create', 'update', 'delete' order lines for other org/lib
    login_user_via_session(client, librarian_martigny.user)
    res = client.get(acq_oline_martigny_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert data['create']['can']
    assert data['update']['can']
    assert data['delete']['can']

    res = client.get(acq_oline_saxon_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert not data['read']['can']
    assert data['list']['can']
    assert not data['update']['can']
    assert not data['delete']['can']

    res = client.get(acq_oline_sion_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert not data['read']['can']
    assert data['list']['can']
    assert not data['update']['can']
    assert not data['delete']['can']

    # Logged as system librarian
    #   * sys_lib can do everything about order lines of its own organisation
    #   * sys_lib can't do anything about order lines of other organisation
    login_user_via_session(client, system_librarian_martigny.user)
    res = client.get(acq_oline_saxon_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert data['create']['can']
    assert data['update']['can']
    assert data['delete']['can']

    res = client.get(acq_oline_sion_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert not data['read']['can']
    assert not data['update']['can']
    assert not data['delete']['can']


def test_order_lines_permissions(patron_martigny,
                                 librarian_martigny,
                                 system_librarian_martigny,
                                 document, org_martigny, lib_sion,
                                 vendor2_martigny,
                                 acq_order_line_fiction_sion,
                                 acq_order_line_fiction_saxon,
                                 acq_order_line_fiction_martigny):
    """Test order lines permissions class."""

    # Anonymous user
    assert not AcqOrderLinePermission.list(None, {})
    assert not AcqOrderLinePermission.read(None, {})
    assert not AcqOrderLinePermission.create(None, {})
    assert not AcqOrderLinePermission.update(None, {})
    assert not AcqOrderLinePermission.delete(None, {})

    # As non Librarian
    acq_oline_martigny = acq_order_line_fiction_martigny
    acq_oline_saxon = acq_order_line_fiction_saxon
    acq_oline_sion = acq_order_line_fiction_sion

    assert not AcqOrderLinePermission.list(None, acq_oline_martigny)
    assert not AcqOrderLinePermission.read(None, acq_oline_martigny)
    assert not AcqOrderLinePermission.create(None, acq_oline_martigny)
    assert not AcqOrderLinePermission.update(None, acq_oline_martigny)
    assert not AcqOrderLinePermission.delete(None, acq_oline_martigny)

    # As Librarian
    with mock.patch(
        'rero_ils.modules.permissions.current_librarian',
        librarian_martigny
    ):
        assert AcqOrderLinePermission.list(None, acq_oline_martigny)
        assert AcqOrderLinePermission.read(None, acq_oline_martigny)
        assert AcqOrderLinePermission.create(None, acq_oline_martigny)
        assert AcqOrderLinePermission.update(None, acq_oline_martigny)
        assert AcqOrderLinePermission.delete(None, acq_oline_martigny)

        assert not AcqOrderLinePermission.read(None, acq_oline_saxon)
        assert not AcqOrderLinePermission.create(None, acq_oline_saxon)
        assert not AcqOrderLinePermission.update(None, acq_oline_saxon)
        assert not AcqOrderLinePermission.delete(None, acq_oline_saxon)

        assert not AcqOrderLinePermission.read(None, acq_oline_sion)
        assert not AcqOrderLinePermission.create(None, acq_oline_sion)
        assert not AcqOrderLinePermission.update(None, acq_oline_sion)
        assert not AcqOrderLinePermission.delete(None, acq_oline_sion)

    # As System-librarian
    with mock.patch(
        'rero_ils.modules.permissions.current_librarian',
        system_librarian_martigny
    ):
        assert AcqOrderLinePermission.list(None, acq_oline_saxon)
        assert AcqOrderLinePermission.read(None, acq_oline_saxon)
        assert AcqOrderLinePermission.create(None, acq_oline_saxon)
        assert AcqOrderLinePermission.update(None, acq_oline_saxon)
        assert AcqOrderLinePermission.delete(None, acq_oline_saxon)

        assert not AcqOrderLinePermission.read(None, acq_oline_sion)
        assert not AcqOrderLinePermission.create(None, acq_oline_sion)
        assert not AcqOrderLinePermission.update(None, acq_oline_sion)
        assert not AcqOrderLinePermission.delete(None, acq_oline_sion)
