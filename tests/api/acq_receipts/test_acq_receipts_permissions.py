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

from rero_ils.modules.acq_receipts.permissions import AcqReceiptPermission


def test_receipts_permissions_api(client, org_martigny, vendor2_martigny,
                                  patron_martigny, system_librarian_martigny,
                                  librarian_martigny,
                                  acq_receipt_fiction_martigny,
                                  acq_receipt_fiction_saxon,
                                  acq_receipt_fiction_sion):
    """Test orders receipt permissions api."""
    acq_receipt_permissions_url = url_for(
        'api_blueprint.permissions',
        route_name='acq_receipts'
    )
    acq_receipt_martigny_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='acq_receipts',
        record_pid=acq_receipt_fiction_martigny.pid
    )
    acq_receipt_saxon_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='acq_receipts',
        record_pid=acq_receipt_fiction_saxon.pid
    )
    acq_receipt_sion_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='acq_receipts',
        record_pid=acq_receipt_fiction_sion.pid
    )

    # Not logged
    res = client.get(acq_receipt_permissions_url)
    assert res.status_code == 401

    # Logged as patron
    login_user_via_session(client, patron_martigny.user)
    res = client.get(acq_receipt_permissions_url)
    assert res.status_code == 403

    # Logged as librarian
    #   * lib can 'list' and 'read' receipts of its own organisation
    #   * lib can 'create', 'update', delete only for its library
    #   * lib can't 'read' acq_receipts of others organisation.
    #   * lib can't 'create', 'update', 'delete' receipt for other org/lib
    login_user_via_session(client, librarian_martigny.user)
    res = client.get(acq_receipt_martigny_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert data['create']['can']
    assert data['update']['can']
    assert data['delete']['can']

    res = client.get(acq_receipt_saxon_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert not data['read']['can']
    assert data['list']['can']
    assert not data['update']['can']
    assert not data['delete']['can']

    res = client.get(acq_receipt_sion_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert not data['read']['can']
    assert data['list']['can']
    assert not data['update']['can']
    assert not data['delete']['can']

    # Logged as system librarian
    #   * sys_lib can do everything about receipts of its own organisation
    #   * sys_lib can't do anything about receipts of other organisation
    login_user_via_session(client, system_librarian_martigny.user)
    res = client.get(acq_receipt_saxon_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert data['create']['can']
    assert data['update']['can']
    assert data['delete']['can']

    res = client.get(acq_receipt_sion_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert not data['read']['can']
    assert not data['update']['can']
    assert not data['delete']['can']


def test_receipts_permissions(patron_martigny, librarian_martigny,
                              system_librarian_martigny,
                              org_martigny, vendor2_martigny,
                              acq_receipt_fiction_sion,
                              acq_receipt_fiction_saxon,
                              acq_receipt_fiction_martigny):
    """Test receipt permissions class."""

    # Anonymous user
    assert not AcqReceiptPermission.list(None, {})
    assert not AcqReceiptPermission.read(None, {})
    assert not AcqReceiptPermission.create(None, {})
    assert not AcqReceiptPermission.update(None, {})
    assert not AcqReceiptPermission.delete(None, {})

    # As non Librarian
    acq_receipt_martigny = acq_receipt_fiction_martigny
    acq_receipt_saxon = acq_receipt_fiction_saxon
    acq_receipt_sion = acq_receipt_fiction_sion
    assert not AcqReceiptPermission.list(None, acq_receipt_martigny)
    assert not AcqReceiptPermission.read(None, acq_receipt_martigny)
    assert not AcqReceiptPermission.create(None, acq_receipt_martigny)
    assert not AcqReceiptPermission.update(None, acq_receipt_martigny)
    assert not AcqReceiptPermission.delete(None, acq_receipt_martigny)

    # As Librarian
    with mock.patch(
        'rero_ils.modules.permissions.current_librarian',
        librarian_martigny
    ):
        assert AcqReceiptPermission.list(None, acq_receipt_martigny)
        assert AcqReceiptPermission.read(None, acq_receipt_martigny)
        assert AcqReceiptPermission.create(None, acq_receipt_martigny)
        assert AcqReceiptPermission.update(None, acq_receipt_martigny)
        assert AcqReceiptPermission.delete(None, acq_receipt_martigny)

        assert not AcqReceiptPermission.read(None, acq_receipt_saxon)
        assert not AcqReceiptPermission.create(None, acq_receipt_saxon)
        assert not AcqReceiptPermission.update(None, acq_receipt_saxon)
        assert not AcqReceiptPermission.delete(None, acq_receipt_saxon)

        assert not AcqReceiptPermission.read(None, acq_receipt_sion)
        assert not AcqReceiptPermission.create(None, acq_receipt_sion)
        assert not AcqReceiptPermission.update(None, acq_receipt_sion)
        assert not AcqReceiptPermission.delete(None, acq_receipt_sion)

    # As System-librarian
    with mock.patch(
        'rero_ils.modules.permissions.current_librarian',
        system_librarian_martigny
    ):
        assert AcqReceiptPermission.list(None, acq_receipt_saxon)
        assert AcqReceiptPermission.read(None, acq_receipt_saxon)
        assert AcqReceiptPermission.create(None, acq_receipt_saxon)
        assert AcqReceiptPermission.update(None, acq_receipt_saxon)
        assert AcqReceiptPermission.delete(None, acq_receipt_saxon)

        assert not AcqReceiptPermission.read(None, acq_receipt_sion)
        assert not AcqReceiptPermission.create(None, acq_receipt_sion)
        assert not AcqReceiptPermission.update(None, acq_receipt_sion)
        assert not AcqReceiptPermission.delete(None, acq_receipt_sion)
