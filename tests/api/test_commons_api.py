# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
# Copyright (C) 2019-2022 UCLouvain
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

"""Tests Commons RERO-ILS REST API."""
import mock
from flask import url_for
from flask_principal import Identity, RoleNeed
from invenio_access import ActionUsers, Permission
from invenio_accounts.testutils import login_user_via_session
from utils import get_json, mock_response, postdata

from rero_ils.modules.acquisition.budgets.permissions import \
    search_action as budget_search_action
from rero_ils.modules.permissions import PermissionContext, can_use_debug_mode
from rero_ils.modules.users.models import UserRole
from rero_ils.permissions import librarian_delete_permission_factory


def test_librarian_delete_permission_factory(
        client, librarian_fully, org_martigny, lib_martigny):
    """Test librarian_delete_permission_factory """
    login_user_via_session(client, librarian_fully.user)
    assert type(librarian_delete_permission_factory(
        None,
        credentials_only=True
    )) == Permission
    assert librarian_delete_permission_factory(org_martigny) is not None


def test_system_librarian_permissions(
        client, json_header, system_librarian_martigny,
        patron_martigny, patron_type_adults_martigny,
        librarian_fully):
    """Test system_librarian permissions."""
    # Login as system_librarian
    login_user_via_session(client, system_librarian_martigny.user)

    # can manage all types of patron roles
    role_url = url_for('api_patrons.get_roles_management_permissions')
    res = client.get(role_url)
    assert res.status_code == 200
    data = get_json(res)
    assert UserRole.FULL_PERMISSIONS in data['allowed_roles']


def test_permission_exposition(app, db, client, system_librarian_martigny):
    """Test permission exposition."""
    login_user_via_session(client, system_librarian_martigny.user)

    # test exposition by role =================================================
    res = client.get(url_for(
        'api_blueprint.permissions_by_role',
        role='dummy-role'
    ))
    data = get_json(res)
    assert res.status_code == 200
    assert not data

    res = client.get(url_for(
        'api_blueprint.permissions_by_role',
        role=UserRole.PROFESSIONAL_READ_ONLY
    ))
    data = get_json(res)
    assert res.status_code == 200
    assert UserRole.PROFESSIONAL_READ_ONLY in data

    res = client.get(url_for(
        'api_blueprint.permissions_by_role',
        role=UserRole.PROFESSIONAL_ROLES
    ))
    data = get_json(res)
    assert res.status_code == 200
    assert all(role in data for role in UserRole.PROFESSIONAL_ROLES)

    # test exposition by patron ===============================================
    res = client.get(url_for(
        'api_blueprint.permissions_by_patron',
        patron_pid=system_librarian_martigny.pid
    ))
    data = get_json(res)
    assert res.status_code == 200
    assert len(data) == len(app.extensions['invenio-access'].actions)

    # system librarian should access to 'can-use-debug-mode'
    perm = [p for p in data if p['name'] == can_use_debug_mode.value][0]
    assert perm['can']
    # add a restriction specific for this user
    db.session.add(ActionUsers.deny(
        can_use_debug_mode,
        user_id=system_librarian_martigny.user.id
    ))
    db.session.commit()
    res = client.get(url_for(
        'api_blueprint.permissions_by_patron',
        patron_pid=system_librarian_martigny.pid
    ))
    data = get_json(res)
    assert res.status_code == 200
    perm = [p for p in data if p['name'] == can_use_debug_mode.value][0]
    assert not perm['can']
    # reset DB
    ActionUsers\
        .query_by_action(can_use_debug_mode)\
        .filter(ActionUsers.user_id == system_librarian_martigny.user.id)\
        .delete(synchronize_session=False)
    db.session.commit()


def test_permission_management(client, system_librarian_martigny):
    """Test permission management."""

    # Test bad usage of the API
    #   1) Anonymous user can't manage permissions.
    #   2) try with bad payload data
    #   3) try with not implemented context
    #   4) try with bad parameters
    res, _ = postdata(client, 'api_blueprint.permission_management', {})
    assert res.status_code == 401

    login_user_via_session(client, system_librarian_martigny.user)
    res, data = postdata(client, 'api_blueprint.permission_management', {})
    assert res.status_code == 400
    assert 'context' in data['message']
    res, data = postdata(client, 'api_blueprint.permission_management', dict(
        context=PermissionContext.BY_ROLE,
        permission=budget_search_action.value,
    ))
    assert res.status_code == 400
    assert 'role_name' in data['message']

    res, data = postdata(client, 'api_blueprint.permission_management', dict(
        context=PermissionContext.BY_USER,
        permission=budget_search_action.value
    ))
    assert res.status_code == 501

    res, data = postdata(client, 'api_blueprint.permission_management', dict(
        context=PermissionContext.BY_ROLE,
        permission='unknown-permission',
        role_name=UserRole.PROFESSIONAL_READ_ONLY
    ))
    assert res.status_code == 400
    assert 'not found' in data['message']
    res, data = postdata(client, 'api_blueprint.permission_management', dict(
        context=PermissionContext.BY_ROLE,
        permission=budget_search_action.value,
        role_name='dummy-role'
    ))
    assert res.status_code == 400
    assert 'not found' in data['message']

    # Real test begin now
    #  1) test user has permission
    #  2) delete this permission using API and test the permission
    #  3) add the permission using API and test it again.
    fake_identity = Identity("fake-id")
    fake_identity.provides.add(RoleNeed(UserRole.PROFESSIONAL_READ_ONLY))
    permission = Permission(budget_search_action)
    assert fake_identity.can(permission)

    perm_url = url_for('api_blueprint.permission_management')
    perm_data = dict(
        context=PermissionContext.BY_ROLE,
        permission=budget_search_action.value,
        role_name=UserRole.PROFESSIONAL_READ_ONLY
    )
    res = client.delete(perm_url, json=perm_data)
    assert res.status_code == 204
    assert not fake_identity.can(permission)

    res = client.post(perm_url, json=perm_data)
    assert res.status_code == 200
    assert fake_identity.can(permission)


@mock.patch('rero_ils.modules.decorators.login_and_librarian',
            mock.MagicMock())
@mock.patch('requests.get')
def test_proxy(mock_get, client):
    """Test proxy."""
    response = client.get(url_for('api_blueprint.proxy'))
    assert response.status_code == 400
    assert response.json['message'] == 'Missing `url` parameter'

    mock_get.return_value = mock_response(status=418)
    response = client.get(url_for(
        'api_blueprint.proxy',
        url='http://mocked.url')
    )
    assert response.status_code == 418
