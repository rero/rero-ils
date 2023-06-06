# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
# Copyright (C) 2019-2023 UCLouvain
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

from flask import current_app, url_for
from flask_principal import AnonymousIdentity, identity_changed
from flask_security.utils import login_user
from invenio_accounts.testutils import login_user_via_session
from utils import check_permission, get_json

from rero_ils.modules.entities.remote_entities.permissions import \
    RemoteEntityPermissionPolicy


def test_remote_entity_permissions_api(client, patron_martigny,
                                       entity_person,
                                       librarian_martigny):
    """Test entities permissions api."""
    prs_permissions_url = url_for(
        'api_blueprint.permissions',
        route_name='remote_entities'
    )
    prs_real_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='remote_entities',
        record_pid=entity_person.pid
    )

    # Not logged
    res = client.get(prs_permissions_url)
    assert res.status_code == 401

    # Logged as patron
    login_user_via_session(client, patron_martigny.user)
    res = client.get(prs_permissions_url)
    assert res.status_code == 403

    # Logged as librarian
    login_user_via_session(client, librarian_martigny.user)
    res = client.get(prs_real_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert not data['create']['can']
    assert not data['update']['can']
    assert not data['delete']['can']


def test_remote_entity_permissions(patron_martigny,
                                   librarian_martigny,
                                   system_librarian_martigny):
    """Test entity permissions class."""
    permission_policy = RemoteEntityPermissionPolicy

    # Anonymous user
    #   - Allow search/read actions on any entity
    #   - Deny create/update/delete actions on any entity
    identity_changed.send(
        current_app._get_current_object(), identity=AnonymousIdentity()
    )
    check_permission(permission_policy, {
        'search': True,
        'read': True,
        'create': False,
        'update': False,
        'delete': False
    }, {})
    # Patron user
    #   - Allow search/read actions on any entity
    #   - Deny create/update/delete actions on any entity
    login_user(patron_martigny.user)
    check_permission(permission_policy, {
        'search': True,
        'read': True,
        'create': False,
        'update': False,
        'delete': False
    }, {})
    # Full permission user
    #   - Allow search/read actions on any entity
    #   - Deny create/update/delete actions on any entity
    login_user(system_librarian_martigny.user)
    check_permission(permission_policy, {
        'search': True,
        'read': True,
        'create': False,
        'update': False,
        'delete': False
    }, {})
