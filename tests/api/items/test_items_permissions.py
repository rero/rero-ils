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

from rero_ils.modules.items.permissions import ItemPermission


def test_items_permissions_api(client, patron_martigny_no_email,
                               system_librarian_martigny_no_email,
                               librarian_martigny_no_email,
                               item_lib_martigny, item_lib_saxon,
                               item_lib_sion):
    """Test items permissions api."""
    item_permissions_url = url_for(
        'api_blueprint.permissions',
        route_name='items'
    )
    item_martigny_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='items',
        record_pid=item_lib_martigny.pid
    )
    item_saxon_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='items',
        record_pid=item_lib_saxon.pid
    )
    item_sion_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='items',
        record_pid=item_lib_sion.pid
    )

    # Not logged
    res = client.get(item_permissions_url)
    assert res.status_code == 401

    # Logged as patron
    login_user_via_session(client, patron_martigny_no_email.user)
    res = client.get(item_permissions_url)
    assert res.status_code == 403

    # Logged as librarian
    #   * lib can 'list' and 'read' item of its own organisation
    #   * lib can 'create', 'update', delete only for its library
    #   * lib can't 'read' item of others organisation.
    #   * lib can't 'create', 'update', 'delete' item for other org/lib
    login_user_via_session(client, librarian_martigny_no_email.user)
    res = client.get(item_martigny_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert data['create']['can']
    assert data['update']['can']
    assert data['delete']['can']

    res = client.get(item_saxon_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert not data['update']['can']
    assert not data['delete']['can']

    res = client.get(item_sion_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert not data['update']['can']
    assert not data['delete']['can']

    # Logged as system librarian
    #   * sys_lib can do everything about patron of its own organisation
    #   * sys_lib can't do anything about patron of other organisation
    login_user_via_session(client, system_librarian_martigny_no_email.user)
    res = client.get(item_saxon_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert data['create']['can']
    assert data['update']['can']
    assert data['delete']['can']

    res = client.get(item_sion_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert not data['update']['can']
    assert not data['delete']['can']


def test_items_permissions(patron_martigny_no_email, org_martigny,
                           librarian_martigny_no_email,
                           system_librarian_martigny_no_email,
                           item_lib_sion, item_lib_saxon, item_lib_martigny):
    """Test item permissions class."""

    # Anonymous user
    assert ItemPermission.list(None, {})
    assert ItemPermission.read(None, {})
    assert not ItemPermission.create(None, {})
    assert not ItemPermission.update(None, {})
    assert not ItemPermission.delete(None, {})

    # As Patron
    with mock.patch(
        'rero_ils.modules.items.permissions.current_patron',
        patron_martigny_no_email
    ):
        assert ItemPermission.list(None, item_lib_martigny)
        assert ItemPermission.read(None, item_lib_martigny)
        assert not ItemPermission.create(None, item_lib_martigny)
        assert not ItemPermission.update(None, item_lib_martigny)
        assert not ItemPermission.delete(None, item_lib_martigny)

    # As Librarian
    with mock.patch(
        'rero_ils.modules.items.permissions.current_patron',
        librarian_martigny_no_email
    ), mock.patch(
        'rero_ils.modules.items.permissions.current_organisation',
        org_martigny
    ):
        assert ItemPermission.list(None, item_lib_martigny)
        assert ItemPermission.read(None, item_lib_martigny)
        assert ItemPermission.create(None, item_lib_martigny)
        assert ItemPermission.update(None, item_lib_martigny)
        assert ItemPermission.delete(None, item_lib_martigny)

        assert ItemPermission.read(None, item_lib_saxon)
        assert not ItemPermission.create(None, item_lib_saxon)
        assert not ItemPermission.update(None, item_lib_saxon)
        assert not ItemPermission.delete(None, item_lib_saxon)

        assert ItemPermission.read(None, item_lib_sion)
        assert not ItemPermission.create(None, item_lib_sion)
        assert not ItemPermission.update(None, item_lib_sion)
        assert not ItemPermission.delete(None, item_lib_sion)

    # As System-librarian
    with mock.patch(
        'rero_ils.modules.items.permissions.current_patron',
        system_librarian_martigny_no_email
    ), mock.patch(
        'rero_ils.modules.items.permissions.current_organisation',
        org_martigny
    ):
        assert ItemPermission.list(None, item_lib_saxon)
        assert ItemPermission.read(None, item_lib_saxon)
        assert ItemPermission.create(None, item_lib_saxon)
        assert ItemPermission.update(None, item_lib_saxon)
        assert ItemPermission.delete(None, item_lib_saxon)

        assert ItemPermission.read(None, item_lib_sion)
        assert not ItemPermission.create(None, item_lib_sion)
        assert not ItemPermission.update(None, item_lib_sion)
        assert not ItemPermission.delete(None, item_lib_sion)
