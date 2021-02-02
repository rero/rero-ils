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

from rero_ils.modules.patron_transaction_events.permissions import \
    PatronTransactionEventPermission


def test_ptre_permissions_api(client, patron_martigny,
                              system_librarian_martigny,
                              librarian_martigny,
                              patron_transaction_overdue_event_martigny,
                              patron_transaction_overdue_event_saxon,
                              patron_transaction_overdue_event_sion):
    """Test patron transactions event permissions api."""
    ptre_permissions_url = url_for(
        'api_blueprint.permissions',
        route_name='patron_transaction_events'
    )
    ptre_martigny_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='patron_transaction_events',
        record_pid=patron_transaction_overdue_event_martigny.pid
    )
    ptre_saxon_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='patron_transaction_events',
        record_pid=patron_transaction_overdue_event_saxon.pid
    )
    ptre_sion_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='patron_transaction_events',
        record_pid=patron_transaction_overdue_event_sion.pid
    )

    # Not logged
    res = client.get(ptre_permissions_url)
    assert res.status_code == 401

    # Logged as patron
    login_user_via_session(client, patron_martigny.user)
    res = client.get(ptre_permissions_url)
    assert res.status_code == 403

    # Logged as librarian
    #   * lib can 'list' and 'read' pttr of its own organisation
    #   * lib can 'create', 'update', 'delete' only for its library
    #   * lib can't 'read' acq_account of others organisation.
    #   * lib can't 'create', 'update', 'delete' acq_account for other org/lib
    login_user_via_session(client, librarian_martigny.user)
    res = client.get(ptre_martigny_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert data['create']['can']
    assert data['update']['can']
    # 'delete' should be true but return false because an event is linked
    # assert data['delete']['can']

    res = client.get(ptre_saxon_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert data['update']['can']
    # 'delete' should be true but return false because an event is linked
    # assert not data['delete']['can']

    res = client.get(ptre_sion_permission_url)
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
    res = client.get(ptre_saxon_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert data['create']['can']
    assert data['update']['can']
    # 'delete' should be true but return false because an event is linked
    # assert data['delete']['can']

    res = client.get(ptre_sion_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert not data['read']['can']
    assert not data['update']['can']
    assert not data['delete']['can']


def test_ptre_permissions(patron_martigny,
                          librarian_martigny,
                          system_librarian_martigny,
                          org_martigny, patron_transaction_overdue_event_saxon,
                          patron_transaction_overdue_event_sion,
                          patron_transaction_overdue_event_martigny):
    """Test patron transaction event permissions class."""

    # Anonymous user
    assert not PatronTransactionEventPermission.list(None, {})
    assert not PatronTransactionEventPermission.read(None, {})
    assert not PatronTransactionEventPermission.create(None, {})
    assert not PatronTransactionEventPermission.update(None, {})
    assert not PatronTransactionEventPermission.delete(None, {})

    # As Patron
    ptre_m = patron_transaction_overdue_event_martigny
    ptre_sa = patron_transaction_overdue_event_saxon
    ptre_si = patron_transaction_overdue_event_sion
    with mock.patch(
        'rero_ils.modules.patron_transactions.permissions.current_patron',
        patron_martigny
    ), mock.patch(
        'rero_ils.modules.patron_transactions.permissions.current_user',
        patron_martigny.user
    ):
        assert PatronTransactionEventPermission.list(None, ptre_m)
        assert PatronTransactionEventPermission.read(None, ptre_m)
        assert not PatronTransactionEventPermission.create(None, ptre_m)
        assert not PatronTransactionEventPermission.update(None, ptre_m)
        assert not PatronTransactionEventPermission.delete(None, ptre_m)

    # As Librarian
    with mock.patch(
        'rero_ils.modules.patron_transactions.permissions.current_patron',
        librarian_martigny
    ), mock.patch(
        'rero_ils.modules.patron_transactions.permissions.current_user',
        librarian_martigny.user
    ), mock.patch(
        'rero_ils.modules.patron_transactions.permissions.'
        'current_organisation',
        org_martigny
    ):
        assert PatronTransactionEventPermission.list(None, ptre_m)
        assert PatronTransactionEventPermission.read(None, ptre_m)
        assert PatronTransactionEventPermission.create(None, ptre_m)
        assert PatronTransactionEventPermission.update(None, ptre_m)
        assert PatronTransactionEventPermission.delete(None, ptre_m)

        assert PatronTransactionEventPermission.read(None, ptre_sa)
        assert PatronTransactionEventPermission.create(None, ptre_sa)
        assert PatronTransactionEventPermission.update(None, ptre_sa)
        assert PatronTransactionEventPermission.delete(None, ptre_sa)

        assert not PatronTransactionEventPermission.read(None, ptre_si)
        assert not PatronTransactionEventPermission.create(None, ptre_si)
        assert not PatronTransactionEventPermission.update(None, ptre_si)
        assert not PatronTransactionEventPermission.delete(None, ptre_si)

    # As System-librarian
    with mock.patch(
        'rero_ils.modules.patron_transactions.permissions.current_patron',
        system_librarian_martigny
    ), mock.patch(
        'rero_ils.modules.patron_transactions.permissions.current_user',
        system_librarian_martigny.user
    ), mock.patch(
        'rero_ils.modules.patron_transactions.permissions.'
        'current_organisation',
        org_martigny
    ):
        assert PatronTransactionEventPermission.list(None, ptre_sa)
        assert PatronTransactionEventPermission.read(None, ptre_sa)
        assert PatronTransactionEventPermission.create(None, ptre_sa)
        assert PatronTransactionEventPermission.update(None, ptre_sa)
        assert PatronTransactionEventPermission.delete(None, ptre_sa)

        assert not PatronTransactionEventPermission.read(None, ptre_si)
        assert not PatronTransactionEventPermission.create(None, ptre_si)
        assert not PatronTransactionEventPermission.update(None, ptre_si)
        assert not PatronTransactionEventPermission.delete(None, ptre_si)
