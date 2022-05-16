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

from rero_ils.modules.circ_policies.permissions import \
    CirculationPolicyPermission


def test_circ_policies_permissions_api(client, librarian_martigny,
                                       system_librarian_martigny,
                                       circ_policy_short_martigny,
                                       circ_policy_temp_martigny,
                                       circ_policy_default_sion):
    """Test circulation policies permissions api."""
    cipo_permissions_url = url_for(
        'api_blueprint.permissions',
        route_name='circ_policies'
    )
    cipo_martigny_permissions_url = url_for(
        'api_blueprint.permissions',
        route_name='circ_policies',
        record_pid=circ_policy_short_martigny.pid
    )
    cipo_tmp_martigny_permissions_url = url_for(
        'api_blueprint.permissions',
        route_name='circ_policies',
        record_pid=circ_policy_temp_martigny.pid
    )
    cipo_sion_permissions_url = url_for(
        'api_blueprint.permissions',
        route_name='circ_policies',
        record_pid=circ_policy_default_sion.pid
    )

    # Not logged
    res = client.get(cipo_permissions_url)
    assert res.status_code == 401

    # Logged as librarian
    #   * lib can 'list' cipo
    #   * lib can 'read' cipo from its own organisation
    #   * lib can't never 'create', 'delete', cipo
    #   * lib can update cipo depending of cipo settings
    login_user_via_session(client, librarian_martigny.user)
    res = client.get(cipo_martigny_permissions_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['list']['can']
    assert data['read']['can']
    assert not data['create']['can']
    assert data['update']['can']
    assert not data['delete']['can']
    res = client.get(cipo_tmp_martigny_permissions_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['update']['can']
    res = client.get(cipo_sion_permissions_url)
    data = get_json(res)
    assert not data['read']['can']

    # Logged as system librarian
    #   * sys_lib can do anything about patron type for its own organisation
    #   * sys_lib can't doo anything about patron type for other organisation
    login_user_via_session(client, system_librarian_martigny.user)
    res = client.get(cipo_martigny_permissions_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['list']['can']
    assert data['read']['can']
    assert data['create']['can']
    assert data['update']['can']
    assert data['delete']['can']
    res = client.get(cipo_sion_permissions_url)
    assert res.status_code == 200
    data = get_json(res)
    assert not data['update']['can']
    assert not data['delete']['can']


def test_circ_policies_permissions(patron_martigny,
                                   librarian_martigny,
                                   system_librarian_martigny,
                                   circ_policy_short_martigny,
                                   circ_policy_temp_martigny, org_martigny):
    """Test circulation policies permission class."""

    # Anonymous user
    assert not CirculationPolicyPermission.list(None, {})
    assert not CirculationPolicyPermission.read(None, {})
    assert not CirculationPolicyPermission.create(None, {})
    assert not CirculationPolicyPermission.update(None, {})
    assert not CirculationPolicyPermission.delete(None, {})

    # As non Librarian
    cipo = circ_policy_short_martigny
    cipo_tmp = circ_policy_temp_martigny

    assert not CirculationPolicyPermission.list(None, cipo)
    assert not CirculationPolicyPermission.read(None, cipo)
    assert not CirculationPolicyPermission.create(None, cipo)
    assert not CirculationPolicyPermission.update(None, cipo)
    assert not CirculationPolicyPermission.delete(None, cipo)

    # As Librarian
    with mock.patch(
        'rero_ils.modules.circ_policies.permissions.current_librarian',
        librarian_martigny
    ):
        assert CirculationPolicyPermission.list(None, cipo)
        assert CirculationPolicyPermission.read(None, cipo)
        assert not CirculationPolicyPermission.create(None, cipo)
        assert CirculationPolicyPermission.update(None, cipo)
        assert not CirculationPolicyPermission.delete(None, cipo)
        assert CirculationPolicyPermission.update(None, cipo_tmp)

    # As SystemLibrarian
    with mock.patch(
        'rero_ils.modules.circ_policies.permissions.current_librarian',
        system_librarian_martigny
    ):
        assert CirculationPolicyPermission.list(None, cipo)
        assert CirculationPolicyPermission.read(None, cipo)
        assert CirculationPolicyPermission.create(None, cipo)
        assert CirculationPolicyPermission.update(None, cipo)
        assert CirculationPolicyPermission.delete(None, cipo)
