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

from rero_ils.modules.acquisition.acq_accounts.permissions import \
    AcqAccountPermission


def test_acq_accounts_permissions_api(client, patron_martigny,
                                      system_librarian_martigny,
                                      librarian_martigny,
                                      budget_2020_sion,
                                      lib_sion,
                                      acq_account_fiction_martigny,
                                      acq_account_books_saxon,
                                      acq_account_fiction_sion):
    """Test acq_account permissions api."""
    acq_account_permissions_url = url_for(
        'api_blueprint.permissions',
        route_name='acq_accounts'
    )
    acq_account_martigny_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='acq_accounts',
        record_pid=acq_account_fiction_martigny.pid
    )
    acq_account_saxon_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='acq_accounts',
        record_pid=acq_account_books_saxon.pid
    )
    acq_account_sion_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='acq_accounts',
        record_pid=acq_account_fiction_sion.pid
    )

    # Not logged
    res = client.get(acq_account_permissions_url)
    assert res.status_code == 401

    # Logged as patron
    login_user_via_session(client, patron_martigny.user)
    res = client.get(acq_account_permissions_url)
    assert res.status_code == 403

    # Logged as librarian
    #   * lib can 'list' and 'read' acq_account of its own organisation
    #   * lib can 'create', 'update', delete only for its library
    #   * lib can't 'read' acq_account of others organisation.
    #   * lib can't 'create', 'update', 'delete' acq_account for other org/lib
    login_user_via_session(client, librarian_martigny.user)
    res = client.get(acq_account_martigny_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert data['create']['can']
    assert data['update']['can']
    assert data['delete']['can']

    res = client.get(acq_account_saxon_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert not data['read']['can']
    assert data['list']['can']
    assert not data['update']['can']
    assert not data['delete']['can']

    res = client.get(acq_account_sion_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert not data['read']['can']
    assert data['list']['can']
    assert not data['update']['can']
    assert not data['delete']['can']

    # Logged as system librarian
    #   * sys_lib can do everything about acq_account of its own organisation
    #   * sys_lib can't do anything about acq_account of other organisation
    login_user_via_session(client, system_librarian_martigny.user)
    res = client.get(acq_account_saxon_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert data['create']['can']
    assert data['update']['can']
    assert data['delete']['can']

    res = client.get(acq_account_sion_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert not data['read']['can']
    assert not data['update']['can']
    assert not data['delete']['can']


def test_acq_accounts_permissions(patron_martigny,
                                  librarian_martigny,
                                  system_librarian_martigny,
                                  org_martigny, org_sion, lib_sion,
                                  acq_account_fiction_martigny,
                                  acq_account_books_saxon,
                                  acq_account_fiction_sion):
    """Test acq_account permissions class."""

    # Anonymous user
    assert not AcqAccountPermission.list(None, {})
    assert not AcqAccountPermission.read(None, {})
    assert not AcqAccountPermission.create(None, {})
    assert not AcqAccountPermission.update(None, {})
    assert not AcqAccountPermission.delete(None, {})

    # As non Librarian
    acq_account_martigny = acq_account_fiction_martigny
    acq_account_saxon = acq_account_books_saxon
    acq_account_sion = acq_account_fiction_sion

    assert not AcqAccountPermission.list(None, acq_account_martigny)
    assert not AcqAccountPermission.read(None, acq_account_martigny)
    assert not AcqAccountPermission.create(None, acq_account_martigny)
    assert not AcqAccountPermission.update(None, acq_account_martigny)
    assert not AcqAccountPermission.delete(None, acq_account_martigny)

    # As Librarian
    with mock.patch(
        'rero_ils.modules.permissions.current_librarian',
        librarian_martigny
    ):
        assert AcqAccountPermission.list(None, acq_account_martigny)
        assert AcqAccountPermission.read(None, acq_account_martigny)
        assert AcqAccountPermission.create(None, acq_account_martigny)
        assert AcqAccountPermission.update(None, acq_account_martigny)
        assert AcqAccountPermission.delete(None, acq_account_martigny)

        assert not AcqAccountPermission.read(None, acq_account_saxon)
        assert not AcqAccountPermission.create(None, acq_account_saxon)
        assert not AcqAccountPermission.update(None, acq_account_saxon)
        assert not AcqAccountPermission.delete(None, acq_account_saxon)

        assert not AcqAccountPermission.read(None, acq_account_sion)
        assert not AcqAccountPermission.create(None, acq_account_sion)
        assert not AcqAccountPermission.update(None, acq_account_sion)
        assert not AcqAccountPermission.delete(None, acq_account_sion)

    # As System-librarian
    with mock.patch(
        'rero_ils.modules.permissions.current_librarian',
        system_librarian_martigny
    ):
        assert AcqAccountPermission.list(None, acq_account_saxon)
        assert AcqAccountPermission.read(None, acq_account_saxon)
        assert AcqAccountPermission.create(None, acq_account_saxon)
        assert AcqAccountPermission.update(None, acq_account_saxon)
        assert AcqAccountPermission.delete(None, acq_account_saxon)

        assert not AcqAccountPermission.read(None, acq_account_sion)
        assert not AcqAccountPermission.create(None, acq_account_sion)
        assert not AcqAccountPermission.update(None, acq_account_sion)
        assert not AcqAccountPermission.delete(None, acq_account_sion)
