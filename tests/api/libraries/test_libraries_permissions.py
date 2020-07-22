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

from rero_ils.modules.libraries.permissions import LibraryPermission


def test_library_permissions_api(client, patron_martigny_no_email,
                                 lib_martigny, lib_sion, lib_saxon,
                                 librarian_martigny_no_email,
                                 system_librarian_martigny_no_email):
    """Test libraries permissions api."""
    lib_permissions_url = url_for(
        'api_blueprint.permissions',
        route_name='libraries'
    )
    lib_martigny_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='libraries',
        record_pid=lib_martigny.pid
    )
    lib_saxon_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='libraries',
        record_pid=lib_saxon.pid
    )
    lib_sion_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='libraries',
        record_pid=lib_sion.pid
    )

    # Not logged
    res = client.get(lib_permissions_url)
    assert res.status_code == 401

    # Logged as patron
    login_user_via_session(client, patron_martigny_no_email.user)
    res = client.get(lib_permissions_url)
    assert res.status_code == 403

    # Logged as librarian
    #   * lib can 'list' and 'read' libraries of its own organisation
    #   * lib can 'create', 'update', delete only for its library
    #   * lib can't 'read' acq_account of others organisation.
    #   * lib can't 'create', 'update', 'delete' acq_account for other org/lib
    login_user_via_session(client, librarian_martigny_no_email.user)
    res = client.get(lib_martigny_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert not data['create']['can']
    assert data['update']['can']
    assert not data['delete']['can']

    res = client.get(lib_saxon_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert not data['update']['can']
    assert not data['delete']['can']

    res = client.get(lib_sion_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert not data['read']['can']
    assert data['list']['can']
    assert not data['update']['can']
    assert not data['delete']['can']

    # Logged as system librarian
    #   * sys_lib can 'list' organisations
    #   * sys_lib can never 'create' and 'delete' any organisation
    #   * sys_lib can 'read' and 'update' only their own organisation
    login_user_via_session(client, system_librarian_martigny_no_email.user)
    res = client.get(lib_saxon_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert data['update']['can']
    assert data['delete']['can']

    res = client.get(lib_sion_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert not data['read']['can']
    assert not data['update']['can']
    assert not data['delete']['can']


def test_library_permissions(patron_martigny_no_email,
                             librarian_martigny_no_email,
                             system_librarian_martigny_no_email,
                             org_martigny, lib_martigny, lib_saxon, lib_sion):
    """Test library permissions class."""

    # Anonymous user
    assert not LibraryPermission.list(None, {})
    assert not LibraryPermission.read(None, {})
    assert not LibraryPermission.create(None, {})
    assert not LibraryPermission.update(None, {})
    assert not LibraryPermission.delete(None, {})

    # As Patron
    with mock.patch(
        'rero_ils.modules.libraries.permissions.current_patron',
        patron_martigny_no_email
    ):
        assert not LibraryPermission.list(None, lib_martigny)
        assert not LibraryPermission.read(None, lib_martigny)
        assert not LibraryPermission.create(None, lib_martigny)
        assert not LibraryPermission.update(None, lib_martigny)
        assert not LibraryPermission.delete(None, lib_martigny)

    # As Librarian
    with mock.patch(
        'rero_ils.modules.libraries.permissions.current_patron',
        librarian_martigny_no_email
    ), mock.patch(
        'rero_ils.modules.libraries.permissions.current_organisation',
        org_martigny
    ):
        assert LibraryPermission.list(None, lib_martigny)
        assert LibraryPermission.read(None, lib_martigny)
        assert not LibraryPermission.create(None, lib_martigny)
        assert LibraryPermission.update(None, lib_martigny)
        assert not LibraryPermission.delete(None, lib_martigny)

        assert LibraryPermission.list(None, lib_saxon)
        assert LibraryPermission.read(None, lib_saxon)
        assert not LibraryPermission.create(None, lib_saxon)
        assert not LibraryPermission.update(None, lib_saxon)
        assert not LibraryPermission.delete(None, lib_saxon)

    # As SystemLibrarian
    with mock.patch(
        'rero_ils.modules.libraries.permissions.current_patron',
        system_librarian_martigny_no_email
    ), mock.patch(
        'rero_ils.modules.libraries.permissions.current_organisation',
        org_martigny
    ):
        assert LibraryPermission.list(None, lib_saxon)
        assert LibraryPermission.read(None, lib_saxon)
        assert LibraryPermission.create(None, lib_saxon)
        assert LibraryPermission.update(None, lib_saxon)
        assert LibraryPermission.delete(None, lib_saxon)

        assert not LibraryPermission.create(None, lib_sion)
        assert not LibraryPermission.update(None, lib_sion)
        assert not LibraryPermission.delete(None, lib_sion)
