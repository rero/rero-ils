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

from rero_ils.modules.patron_transactions.permissions import \
    PatronTransactionPermission


def test_pttr_permissions_api(client, patron_martigny,
                              system_librarian_martigny,
                              librarian_martigny,
                              patron_transaction_overdue_martigny,
                              patron_transaction_overdue_saxon,
                              patron_transaction_overdue_sion):
    """Test patron transactions permissions api."""
    pttr_permissions_url = url_for(
        'api_blueprint.permissions',
        route_name='patron_transactions'
    )
    pttr_martigny_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='patron_transactions',
        record_pid=patron_transaction_overdue_martigny.pid
    )
    pttr_saxon_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='patron_transactions',
        record_pid=patron_transaction_overdue_saxon.pid
    )
    pttr_sion_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='patron_transactions',
        record_pid=patron_transaction_overdue_sion.pid
    )

    # Not logged
    res = client.get(pttr_permissions_url)
    assert res.status_code == 401

    # Logged as patron
    login_user_via_session(client, patron_martigny.user)
    res = client.get(pttr_permissions_url)
    assert res.status_code == 403

    # Logged as librarian
    #   * lib can 'list' and 'read' pttr of its own organisation
    #   * lib can 'create', 'update', 'delete' only for its library
    #   * lib can't 'read' acq_account of others organisation.
    #   * lib can't 'create', 'update', 'delete' acq_account for other org/lib
    login_user_via_session(client, librarian_martigny.user)
    res = client.get(pttr_martigny_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert data['create']['can']
    assert data['update']['can']
    # 'delete' should be true but return false because an event is linked
    # assert data['delete']['can']

    res = client.get(pttr_saxon_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert data['update']['can']
    # 'delete' should be true but return false because an event is linked
    # assert not data['delete']['can']

    res = client.get(pttr_sion_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert not data['read']['can']
    assert data['list']['can']
    assert not data['update']['can']
    assert not data['delete']['can']

    # Logged as system librarian
    #   * sys_lib can do everything about pttr of its own organisation
    #   * sys_lib can't do anything about pttr of other organisation
    login_user_via_session(client, system_librarian_martigny.user)
    res = client.get(pttr_saxon_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert data['create']['can']
    assert data['update']['can']
    # 'delete' should be true but return false because an event is linked
    # assert data['delete']['can']

    res = client.get(pttr_sion_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert not data['read']['can']
    assert not data['update']['can']
    assert not data['delete']['can']


def test_pttr_permissions(patron_martigny,
                          librarian_martigny,
                          system_librarian_martigny,
                          org_martigny, patron_transaction_overdue_saxon,
                          patron_transaction_overdue_sion,
                          patron_transaction_overdue_martigny):
    """Test patron transaction permissions class."""

    # Anonymous user
    assert not PatronTransactionPermission.list(None, {})
    assert not PatronTransactionPermission.read(None, {})
    assert not PatronTransactionPermission.create(None, {})
    assert not PatronTransactionPermission.update(None, {})
    assert not PatronTransactionPermission.delete(None, {})

    # As Patron
    pttr_m = patron_transaction_overdue_martigny
    pttr_sa = patron_transaction_overdue_saxon
    pttr_si = patron_transaction_overdue_sion
    with mock.patch(
        'rero_ils.modules.patron_transactions.permissions.current_patrons',
        [patron_martigny]
    ):
        assert PatronTransactionPermission.list(None, pttr_m)
        assert PatronTransactionPermission.read(None, pttr_m)
        assert not PatronTransactionPermission.create(None, pttr_m)
        assert not PatronTransactionPermission.update(None, pttr_m)
        assert not PatronTransactionPermission.delete(None, pttr_m)

    # As Librarian
    with mock.patch(
        'rero_ils.modules.patron_transactions.permissions.current_librarian',
        librarian_martigny
    ):
        assert PatronTransactionPermission.list(None, pttr_m)
        assert PatronTransactionPermission.read(None, pttr_m)
        assert PatronTransactionPermission.create(None, pttr_m)
        assert PatronTransactionPermission.update(None, pttr_m)
        assert PatronTransactionPermission.delete(None, pttr_m)

        assert PatronTransactionPermission.read(None, pttr_sa)
        assert PatronTransactionPermission.create(None, pttr_sa)
        assert PatronTransactionPermission.update(None, pttr_sa)
        assert PatronTransactionPermission.delete(None, pttr_sa)

        assert not PatronTransactionPermission.read(None, pttr_si)
        assert not PatronTransactionPermission.create(None, pttr_si)
        assert not PatronTransactionPermission.update(None, pttr_si)
        assert not PatronTransactionPermission.delete(None, pttr_si)

    # As System-librarian
    with mock.patch(
        'rero_ils.modules.patron_transactions.permissions.current_librarian',
        system_librarian_martigny
    ):
        assert PatronTransactionPermission.list(None, pttr_sa)
        assert PatronTransactionPermission.read(None, pttr_sa)
        assert PatronTransactionPermission.create(None, pttr_sa)
        assert PatronTransactionPermission.update(None, pttr_sa)
        assert PatronTransactionPermission.delete(None, pttr_sa)

        assert not PatronTransactionPermission.read(None, pttr_si)
        assert not PatronTransactionPermission.create(None, pttr_si)
        assert not PatronTransactionPermission.update(None, pttr_si)
        assert not PatronTransactionPermission.delete(None, pttr_si)
