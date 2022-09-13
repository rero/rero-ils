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

from rero_ils.modules.acquisition.acq_receipt_lines.permissions import \
    AcqReceiptLinePermission


def test_receipt_lines_permissions_api(client, org_martigny, vendor2_martigny,
                                       patron_martigny,
                                       system_librarian_martigny,
                                       librarian_martigny,
                                       acq_receipt_line_1_fiction_martigny,
                                       acq_receipt_line_2_fiction_martigny,
                                       acq_receipt_line_fiction_saxon,
                                       acq_receipt_line_fiction_sion):
    """Test orders receipt lines permissions api."""
    acq_receipt_line_permissions_url = url_for(
        'api_blueprint.permissions',
        route_name='acq_receipt_lines'
    )
    acq_receipt_line_1_martigny_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='acq_receipt_lines',
        record_pid=acq_receipt_line_1_fiction_martigny.pid
    )
    acq_receipt_line_saxon_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='acq_receipt_lines',
        record_pid=acq_receipt_line_fiction_saxon.pid
    )
    acq_receipt_line_sion_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='acq_receipt_lines',
        record_pid=acq_receipt_line_fiction_sion.pid
    )

    # Not logged
    res = client.get(acq_receipt_line_permissions_url)
    assert res.status_code == 401

    # Logged as patron
    login_user_via_session(client, patron_martigny.user)
    res = client.get(acq_receipt_line_permissions_url)
    assert res.status_code == 403

    # Logged as librarian
    #   * lib can 'list' and 'read' receipt lines of its own organisation
    #   * lib can 'create', 'update', delete only for its library
    #   * lib can't 'read' acq_receipt_lines of others organisation.
    #   * lib can't 'create', 'update', 'delete' receiptlines for other org/lib
    login_user_via_session(client, librarian_martigny.user)
    res = client.get(acq_receipt_line_1_martigny_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert data['create']['can']
    assert data['update']['can']
    assert data['delete']['can']

    res = client.get(acq_receipt_line_saxon_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert not data['read']['can']
    assert data['list']['can']
    assert not data['update']['can']
    assert not data['delete']['can']

    res = client.get(acq_receipt_line_sion_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert not data['read']['can']
    assert data['list']['can']
    assert not data['update']['can']
    assert not data['delete']['can']

    # Logged as system librarian
    #   * sys_lib can do everything about receipt lines of its own organisation
    #   * sys_lib can't do anything about receipt lines of other organisation
    login_user_via_session(client, system_librarian_martigny.user)
    res = client.get(acq_receipt_line_saxon_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert data['create']['can']
    assert data['update']['can']
    assert data['delete']['can']

    res = client.get(acq_receipt_line_sion_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert not data['read']['can']
    assert not data['update']['can']
    assert not data['delete']['can']


def test_receipt_lines_permissions(client, org_martigny, vendor2_martigny,
                                   patron_martigny,
                                   system_librarian_martigny,
                                   librarian_martigny,
                                   acq_receipt_line_1_fiction_martigny,
                                   acq_receipt_line_2_fiction_martigny,
                                   acq_receipt_line_fiction_saxon,
                                   acq_receipt_line_fiction_sion):

    """Test receipt line permissions class."""
    # Anonymous user
    assert not AcqReceiptLinePermission.list(None, {})
    assert not AcqReceiptLinePermission.read(None, {})
    assert not AcqReceiptLinePermission.create(None, {})
    assert not AcqReceiptLinePermission.update(None, {})
    assert not AcqReceiptLinePermission.delete(None, {})

    # As non Librarian
    receipt_line_1_martigny = acq_receipt_line_1_fiction_martigny
    receipt_line_saxon = acq_receipt_line_fiction_saxon
    receipt_line_sion = acq_receipt_line_fiction_sion
    assert not AcqReceiptLinePermission.list(None, receipt_line_1_martigny)
    assert not AcqReceiptLinePermission.read(None, receipt_line_1_martigny)
    assert not AcqReceiptLinePermission.create(None, receipt_line_1_martigny)
    assert not AcqReceiptLinePermission.update(None, receipt_line_1_martigny)
    assert not AcqReceiptLinePermission.delete(None, receipt_line_1_martigny)

    # As Librarian
    with mock.patch(
        'rero_ils.modules.permissions.current_librarian',
        librarian_martigny
    ):
        assert AcqReceiptLinePermission.list(None, receipt_line_1_martigny)
        assert AcqReceiptLinePermission.read(None, receipt_line_1_martigny)
        assert AcqReceiptLinePermission.create(None, receipt_line_1_martigny)
        assert AcqReceiptLinePermission.update(None, receipt_line_1_martigny)
        assert AcqReceiptLinePermission.delete(None, receipt_line_1_martigny)

        assert not AcqReceiptLinePermission.read(None, receipt_line_saxon)
        assert not AcqReceiptLinePermission.create(None, receipt_line_saxon)
        assert not AcqReceiptLinePermission.update(None, receipt_line_saxon)
        assert not AcqReceiptLinePermission.delete(None, receipt_line_saxon)

        assert not AcqReceiptLinePermission.read(None, receipt_line_sion)
        assert not AcqReceiptLinePermission.create(None, receipt_line_sion)
        assert not AcqReceiptLinePermission.update(None, receipt_line_sion)
        assert not AcqReceiptLinePermission.delete(None, receipt_line_sion)

    # As System-librarian
    with mock.patch(
        'rero_ils.modules.permissions.current_librarian',
        system_librarian_martigny
    ):
        assert AcqReceiptLinePermission.list(None, receipt_line_saxon)
        assert AcqReceiptLinePermission.read(None, receipt_line_saxon)
        assert AcqReceiptLinePermission.create(None, receipt_line_saxon)
        assert AcqReceiptLinePermission.update(None, receipt_line_saxon)
        assert AcqReceiptLinePermission.delete(None, receipt_line_saxon)

        assert not AcqReceiptLinePermission.read(None, receipt_line_sion)
        assert not AcqReceiptLinePermission.create(None, receipt_line_sion)
        assert not AcqReceiptLinePermission.update(None, receipt_line_sion)
        assert not AcqReceiptLinePermission.delete(None, receipt_line_sion)
