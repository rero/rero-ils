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

from rero_ils.modules.organisations.permissions import OrganisationPermission


def test_organisation_permissions_api(client, patron_martigny,
                                      org_martigny, org_sion,
                                      system_librarian_martigny):
    """Test organisations permissions api."""
    org_permissions_url = url_for(
        'api_blueprint.permissions',
        route_name='organisations'
    )
    org_martigny_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='organisations',
        record_pid=org_martigny.pid
    )
    org_sion_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='organisations',
        record_pid=org_sion.pid
    )

    # Not logged
    res = client.get(org_permissions_url)
    assert res.status_code == 401

    # Logged as patron
    login_user_via_session(client, patron_martigny.user)
    res = client.get(org_permissions_url)
    assert res.status_code == 403

    # Logged as system librarian
    #   * sys_lib can 'list' organisations
    #   * sys_lib can never 'create' and 'delete' any organisation
    #   * sys_lib can 'read' and 'update' only their own organisation
    login_user_via_session(client, system_librarian_martigny.user)
    res = client.get(org_martigny_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert not data['create']['can']
    assert data['update']['can']
    assert not data['delete']['can']

    res = client.get(org_sion_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert not data['read']['can']
    assert not data['update']['can']


def test_organisation_permissions(patron_martigny,
                                  librarian_martigny,
                                  system_librarian_martigny,
                                  org_martigny_data, org_martigny):
    """Test organisation permissions class."""

    # Anonymous user
    assert not OrganisationPermission.list(None, {})
    assert not OrganisationPermission.read(None, {})
    assert not OrganisationPermission.create(None, {})
    assert not OrganisationPermission.update(None, {})
    assert not OrganisationPermission.delete(None, {})

    # As non Librarian
    assert not OrganisationPermission.list(None, org_martigny_data)
    assert not OrganisationPermission.read(None, org_martigny_data)
    assert not OrganisationPermission.create(None, org_martigny_data)
    assert not OrganisationPermission.update(None, org_martigny_data)
    assert not OrganisationPermission.delete(None, org_martigny_data)

    # As Librarian
    with mock.patch(
        'rero_ils.modules.organisations.permissions.current_librarian',
        librarian_martigny
    ):
        assert OrganisationPermission.list(None, org_martigny_data)
        assert OrganisationPermission.read(None, org_martigny_data)
        assert not OrganisationPermission.create(None, org_martigny_data)
        assert not OrganisationPermission.update(None, org_martigny_data)
        assert not OrganisationPermission.delete(None, org_martigny_data)

    # As SystemLibrarian
    with mock.patch(
        'rero_ils.modules.organisations.permissions.current_librarian',
        system_librarian_martigny
    ):
        assert OrganisationPermission.list(None, org_martigny_data)
        assert OrganisationPermission.read(None, org_martigny_data)
        assert not OrganisationPermission.create(None, org_martigny_data)
        assert OrganisationPermission.update(None, org_martigny_data)
        assert not OrganisationPermission.delete(None, org_martigny_data)
