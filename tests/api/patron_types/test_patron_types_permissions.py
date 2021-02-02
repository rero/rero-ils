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

from rero_ils.modules.patron_types.permissions import PatronTypePermission


def test_patron_types_permissions_api(client, librarian_martigny,
                                      system_librarian_martigny,
                                      patron_type_adults_martigny,
                                      patron_type_youngsters_sion):
    """Test patron types permissions api."""
    ptty_permissions_url = url_for(
        'api_blueprint.permissions',
        route_name='patron_types'
    )
    ptty_adult_martigny_permissions_url = url_for(
        'api_blueprint.permissions',
        route_name='patron_types',
        record_pid=patron_type_adults_martigny.pid
    )
    ptty_youngsters_sion_permissions_url = url_for(
        'api_blueprint.permissions',
        route_name='patron_types',
        record_pid=patron_type_youngsters_sion.pid
    )

    # Not logged
    res = client.get(ptty_permissions_url)
    assert res.status_code == 401

    # Logged as librarian
    #   * lib can 'list' patron_type
    #   * lib can 'read' patron_type from its own organisation
    #   * lib can't never 'create', 'delete', 'update' patron_type
    login_user_via_session(client, librarian_martigny.user)
    res = client.get(ptty_adult_martigny_permissions_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['list']['can']
    assert data['read']['can']
    assert not data['create']['can']
    assert not data['update']['can']
    assert not data['delete']['can']
    res = client.get(ptty_youngsters_sion_permissions_url)
    data = get_json(res)
    assert not data['read']['can']

    # Logged as system librarian
    #   * sys_lib can do anything about patron_type for its own organisation
    #   * sys_lib can't do anything about patron_type for other organisation
    login_user_via_session(client, system_librarian_martigny.user)
    res = client.get(ptty_adult_martigny_permissions_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['list']['can']
    assert data['read']['can']
    assert data['create']['can']
    assert data['update']['can']
    assert data['delete']['can']
    res = client.get(ptty_youngsters_sion_permissions_url)
    assert res.status_code == 200
    data = get_json(res)
    assert not data['update']['can']
    assert not data['delete']['can']


def test_patron_types_permissions(patron_martigny,
                                  librarian_martigny,
                                  system_librarian_martigny,
                                  patron_type_adults_martigny, org_martigny):
    """Test patron types permissions class."""

    # Anonymous user
    assert not PatronTypePermission.list(None, {})
    assert not PatronTypePermission.read(None, {})
    assert not PatronTypePermission.create(None, {})
    assert not PatronTypePermission.update(None, {})
    assert not PatronTypePermission.delete(None, {})

    # As Patron
    ptty = patron_type_adults_martigny
    with mock.patch(
        'rero_ils.modules.patron_types.permissions.current_patron',
        patron_martigny
    ), mock.patch(
        'rero_ils.modules.patron_types.permissions.current_organisation',
        org_martigny
    ):
        assert not PatronTypePermission.list(None, ptty)
        assert not PatronTypePermission.read(None, ptty)
        assert not PatronTypePermission.create(None, ptty)
        assert not PatronTypePermission.update(None, ptty)
        assert not PatronTypePermission.delete(None, ptty)

    # As Librarian
    with mock.patch(
        'rero_ils.modules.patron_types.permissions.current_patron',
        librarian_martigny
    ), mock.patch(
        'rero_ils.modules.patron_types.permissions.current_organisation',
        org_martigny
    ):
        assert PatronTypePermission.list(None, ptty)
        assert PatronTypePermission.read(None, ptty)
        assert not PatronTypePermission.create(None, ptty)
        assert not PatronTypePermission.update(None, ptty)
        assert not PatronTypePermission.delete(None, ptty)

    # As SystemLibrarian
    with mock.patch(
        'rero_ils.modules.patron_types.permissions.current_patron',
        system_librarian_martigny
    ), mock.patch(
        'rero_ils.modules.patron_types.permissions.current_organisation',
        org_martigny
    ):
        assert PatronTypePermission.list(None, ptty)
        assert PatronTypePermission.read(None, ptty)
        assert PatronTypePermission.create(None, ptty)
        assert PatronTypePermission.update(None, ptty)
        assert PatronTypePermission.delete(None, ptty)
