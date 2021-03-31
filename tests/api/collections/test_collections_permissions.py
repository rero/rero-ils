# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2020 RERO
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

"""Tests REST API for collections."""

import mock
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import get_json

from rero_ils.modules.collections.permissions import CollectionPermission


def test_collections_permissions_api(client, document,
                                     item_type_standard_martigny,
                                     item_lib_martigny, item2_lib_martigny,
                                     item_lib_sion, item2_lib_sion,
                                     loc_public_martigny, coll_martigny_1,
                                     coll_sion_1, patron_martigny,
                                     system_librarian_martigny,
                                     librarian_martigny):
    """Test collections permissions."""
    coll_permissions_url = url_for(
        'api_blueprint.permissions',
        route_name='collections',
    )

    coll_martigny_permissions_url = url_for(
        'api_blueprint.permissions',
        route_name='collections',
        record_pid=coll_martigny_1.pid
    )

    coll_sion_permissions_url = url_for(
        'api_blueprint.permissions',
        route_name='collections',
        record_pid=coll_sion_1.pid
    )

    # Not logged
    res = client.get(coll_permissions_url)
    assert res.status_code == 401

    # Logged as patron
    login_user_via_session(client, patron_martigny.user)
    res = client.get(coll_permissions_url)
    assert res.status_code == 403
    data = get_json(res)

    # Logged as librarian
    #   * lib can 'list' and 'read' all the collections
    #   * lib can 'create', 'update', delete only for his library
    #   * lib can't 'create', 'update', 'delete' item for other org
    login_user_via_session(client, librarian_martigny.user)
    res = client.get(coll_martigny_permissions_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert data['create']['can']
    assert data['update']['can']
    assert data['delete']['can']

    res = client.get(coll_sion_permissions_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert not data['update']['can']
    assert not data['delete']['can']

    # Logged as system librarian
    #   * sys lib can 'list' and 'read' all the collections
    #   * sys lib can 'create', 'update', delete only for his organisation
    #   * sys lib can't 'create', 'update', 'delete' item for other org
    login_user_via_session(client, system_librarian_martigny.user)
    res = client.get(coll_martigny_permissions_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert data['update']['can']
    assert data['delete']['can']

    res = client.get(coll_sion_permissions_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert not data['update']['can']
    assert not data['delete']['can']


def test_collections_permissions(patron_martigny,
                                 librarian_martigny,
                                 system_librarian_martigny,
                                 coll_martigny_1, coll_sion_1,
                                 coll_saxon_1, lib_martigny, org_martigny):
    """Test collection permissions class."""

    # Anonymous user
    assert CollectionPermission.list(None, {})
    assert CollectionPermission.read(None, {})
    assert not CollectionPermission.create(None, {})
    assert not CollectionPermission.update(None, coll_martigny_1)
    assert not CollectionPermission.delete(None, {})

    # As non Librarian

    assert CollectionPermission.list(None, coll_martigny_1)
    assert CollectionPermission.read(None, coll_martigny_1)
    assert not CollectionPermission.create(None, coll_martigny_1)
    assert not CollectionPermission.update(None, coll_martigny_1)
    assert not CollectionPermission.delete(None, coll_martigny_1)

    # As Librarian
    with mock.patch(
        'rero_ils.modules.collections.permissions.current_librarian',
        librarian_martigny
    ):
        assert CollectionPermission.list(None, coll_martigny_1)
        assert CollectionPermission.read(None, coll_martigny_1)
        assert CollectionPermission.create(None, coll_martigny_1)
        assert CollectionPermission.update(None, coll_martigny_1)
        assert CollectionPermission.delete(None, coll_martigny_1)

        assert CollectionPermission.list(None, coll_saxon_1)
        assert CollectionPermission.read(None, coll_saxon_1)
        assert CollectionPermission.update(None, coll_saxon_1)
        assert CollectionPermission.delete(None, coll_saxon_1)

        assert CollectionPermission.list(None, coll_sion_1)
        assert CollectionPermission.read(None, coll_sion_1)
        assert not CollectionPermission.update(None, coll_sion_1)
        assert not CollectionPermission.delete(None, coll_sion_1)

    # As SystemLibrarian
    with mock.patch(
        'rero_ils.modules.collections.permissions.current_librarian',
        system_librarian_martigny
    ):
        assert CollectionPermission.list(None, coll_martigny_1)
        assert CollectionPermission.read(None, coll_martigny_1)
        assert CollectionPermission.create(None, coll_martigny_1)
        assert CollectionPermission.update(None, coll_martigny_1)
        assert CollectionPermission.delete(None, coll_martigny_1)

        assert CollectionPermission.list(None, coll_saxon_1)
        assert CollectionPermission.read(None, coll_saxon_1)
        assert CollectionPermission.update(None, coll_saxon_1)
        assert CollectionPermission.delete(None, coll_saxon_1)

        assert CollectionPermission.list(None, coll_sion_1)
        assert CollectionPermission.read(None, coll_sion_1)
        assert not CollectionPermission.update(None, coll_sion_1)
        assert not CollectionPermission.delete(None, coll_sion_1)
