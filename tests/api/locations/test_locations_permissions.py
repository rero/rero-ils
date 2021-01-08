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

from rero_ils.modules.locations.permissions import LocationPermission


def test_location_permissions_api(client, patron_martigny_no_email,
                                  loc_public_martigny, loc_public_saxon,
                                  loc_public_sion, librarian_martigny_no_email,
                                  system_librarian_martigny_no_email):
    """Test locations permissions api."""
    loc_permissions_url = url_for(
        'api_blueprint.permissions',
        route_name='locations'
    )
    loc_martigny_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='locations',
        record_pid=loc_public_martigny.pid
    )
    loc_saxon_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='locations',
        record_pid=loc_public_saxon.pid
    )
    loc_sion_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='locations',
        record_pid=loc_public_sion.pid
    )

    # Not logged
    res = client.get(loc_permissions_url)
    assert res.status_code == 401

    # Logged as patron
    login_user_via_session(client, patron_martigny_no_email.user)
    res = client.get(loc_permissions_url)
    assert res.status_code == 403

    # Logged as librarian
    #   * lib can 'list' and 'read' libraries of its own organisation
    #   * lib can 'create', 'update', delete only for its library
    #   * lib can't 'read' acq_account of others organisation.
    #   * lib can't 'create', 'update', 'delete' acq_account for other org/lib
    login_user_via_session(client, librarian_martigny_no_email.user)
    res = client.get(loc_martigny_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert data['create']['can']
    assert data['update']['can']
    assert data['delete']['can']

    res = client.get(loc_saxon_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert not data['update']['can']
    assert not data['delete']['can']

    res = client.get(loc_sion_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert not data['update']['can']
    assert not data['delete']['can']

    # Logged as system librarian
    #   * sys_lib can 'list' organisations
    #   * sys_lib can never 'create' and 'delete' any organisation
    #   * sys_lib can 'read' and 'update' only their own organisation
    login_user_via_session(client, system_librarian_martigny_no_email.user)
    res = client.get(loc_saxon_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert data['update']['can']
    assert data['delete']['can']

    res = client.get(loc_sion_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert not data['update']['can']
    assert not data['delete']['can']


def test_location_permissions(client, patron_martigny_no_email,
                              librarian_martigny_no_email,
                              system_librarian_martigny_no_email,
                              org_martigny, loc_public_martigny,
                              loc_public_saxon, loc_public_sion):
    """Test location permissions class."""

    # Anonymous user
    assert not LocationPermission.list(None, {})
    assert not LocationPermission.read(None, {})
    assert not LocationPermission.create(None, {})
    assert not LocationPermission.update(None, {})
    assert not LocationPermission.delete(None, {})

    # As Patron
    with mock.patch(
        'rero_ils.modules.locations.permissions.current_patron',
        patron_martigny_no_email
    ):
        assert LocationPermission.list(None, loc_public_martigny)
        assert LocationPermission.read(None, loc_public_martigny)
        assert not LocationPermission.create(None, loc_public_martigny)
        assert not LocationPermission.update(None, loc_public_martigny)
        assert not LocationPermission.delete(None, loc_public_martigny)

    # As Librarian
    with mock.patch(
        'rero_ils.modules.locations.permissions.current_patron',
        librarian_martigny_no_email
    ), mock.patch(
        'rero_ils.modules.locations.permissions.current_organisation',
        org_martigny
    ):
        assert LocationPermission.list(None, loc_public_martigny)
        assert LocationPermission.read(None, loc_public_martigny)
        assert LocationPermission.create(None, loc_public_martigny)
        assert LocationPermission.update(None, loc_public_martigny)
        assert LocationPermission.delete(None, loc_public_martigny)

        assert LocationPermission.list(None, loc_public_sion)
        assert LocationPermission.read(None, loc_public_sion)
        assert not LocationPermission.create(None, loc_public_sion)
        assert not LocationPermission.update(None, loc_public_sion)
        assert not LocationPermission.delete(None, loc_public_sion)

    # As SystemLibrarian
    with mock.patch(
        'rero_ils.modules.locations.permissions.current_patron',
        system_librarian_martigny_no_email
    ), mock.patch(
        'rero_ils.modules.locations.permissions.current_organisation',
        org_martigny
    ):
        assert LocationPermission.list(None, loc_public_saxon)
        assert LocationPermission.read(None, loc_public_saxon)
        assert LocationPermission.create(None, loc_public_saxon)
        assert LocationPermission.update(None, loc_public_saxon)
        assert LocationPermission.delete(None, loc_public_saxon)

        assert LocationPermission.read(None, loc_public_sion)
        assert not LocationPermission.create(None, loc_public_sion)
        assert not LocationPermission.update(None, loc_public_sion)
        assert not LocationPermission.delete(None, loc_public_sion)
