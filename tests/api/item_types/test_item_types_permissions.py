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

from rero_ils.modules.item_types.permissions import ItemTypePermission


def test_item_types_permissions_api(client, librarian_martigny,
                                    system_librarian_martigny,
                                    item_type_standard_martigny,
                                    item_type_regular_sion):
    """Test patron types permissions api."""
    itty_permissions_url = url_for(
        'api_blueprint.permissions',
        route_name='item_types'
    )
    itty_martigny_permissions_url = url_for(
        'api_blueprint.permissions',
        route_name='item_types',
        record_pid=item_type_standard_martigny.pid
    )
    itty_sion_permissions_url = url_for(
        'api_blueprint.permissions',
        route_name='item_types',
        record_pid=item_type_regular_sion.pid
    )

    # Not logged
    res = client.get(itty_permissions_url)
    assert res.status_code == 401

    # Logged as librarian
    #   * lib can 'list' item_type
    #   * lib can 'read' item_type from its own organisation
    #   * lib can't never 'create', 'delete', 'update' item_type
    login_user_via_session(client, librarian_martigny.user)
    res = client.get(itty_martigny_permissions_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['list']['can']
    assert data['read']['can']
    assert not data['create']['can']
    assert not data['update']['can']
    assert not data['delete']['can']
    res = client.get(itty_sion_permissions_url)
    data = get_json(res)
    assert not data['read']['can']

    # Logged as system librarian
    #   * sys_lib can do anything about item_type for its own organisation
    #   * sys_lib can't do anything about item_type for other organisation
    login_user_via_session(client, system_librarian_martigny.user)
    res = client.get(itty_martigny_permissions_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['list']['can']
    assert data['read']['can']
    assert data['create']['can']
    assert data['update']['can']
    assert data['delete']['can']
    res = client.get(itty_sion_permissions_url)
    assert res.status_code == 200
    data = get_json(res)
    assert not data['update']['can']
    assert not data['delete']['can']


def test_item_types_permissions(patron_martigny,
                                librarian_martigny,
                                system_librarian_martigny,
                                item_type_standard_martigny, org_martigny):
    """Test patron types permissions class."""

    # Anonymous user
    assert not ItemTypePermission.list(None, {})
    assert not ItemTypePermission.read(None, {})
    assert not ItemTypePermission.create(None, {})
    assert not ItemTypePermission.update(None, {})
    assert not ItemTypePermission.delete(None, {})

    # As non Librarian
    itty = item_type_standard_martigny
    assert not ItemTypePermission.list(None, itty)
    assert not ItemTypePermission.read(None, itty)
    assert not ItemTypePermission.create(None, itty)
    assert not ItemTypePermission.update(None, itty)
    assert not ItemTypePermission.delete(None, itty)

    # As Librarian
    with mock.patch(
        'rero_ils.modules.item_types.permissions.current_librarian',
        librarian_martigny
    ):
        assert ItemTypePermission.list(None, itty)
        assert ItemTypePermission.read(None, itty)
        assert not ItemTypePermission.create(None, itty)
        assert not ItemTypePermission.update(None, itty)
        assert not ItemTypePermission.delete(None, itty)

    # As SystemLibrarian
    with mock.patch(
        'rero_ils.modules.item_types.permissions.current_librarian',
        system_librarian_martigny
    ):
        assert ItemTypePermission.list(None, itty)
        assert ItemTypePermission.read(None, itty)
        assert ItemTypePermission.create(None, itty)
        assert ItemTypePermission.update(None, itty)
        assert ItemTypePermission.delete(None, itty)
