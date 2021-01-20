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

from rero_ils.modules.notifications.permissions import NotificationPermission


def test_notifications_permissions_api(client, patron_martigny,
                                       system_librarian_martigny,
                                       librarian_martigny,
                                       notification_late_martigny,
                                       notification_late_saxon,
                                       notification_late_sion):
    """Test notification permissions api."""
    notif_permissions_url = url_for(
        'api_blueprint.permissions',
        route_name='notifications'
    )
    notif_martigny_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='notifications',
        record_pid=notification_late_martigny.pid
    )
    notif_saxon_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='notifications',
        record_pid=notification_late_saxon.pid
    )
    notif_sion_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='notifications',
        record_pid=notification_late_sion.pid
    )

    # Not logged
    res = client.get(notif_permissions_url)
    assert res.status_code == 401

    # Logged as patron
    login_user_via_session(client, patron_martigny.user)
    res = client.get(notif_permissions_url)
    assert res.status_code == 403

    # Logged as librarian
    #   * lib can 'list' and 'read' notification of its own organisation
    #   * lib can 'create', 'update', 'delete' only for its library
    #   * lib can't 'read' notification of others organisation.
    #   * lib can't 'create', 'update', 'delete' notification for other org/lib
    login_user_via_session(client, librarian_martigny.user)
    res = client.get(notif_martigny_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert data['create']['can']
    assert data['update']['can']
    assert data['delete']['can']

    res = client.get(notif_saxon_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert data['update']['can']
    assert data['delete']['can']

    res = client.get(notif_sion_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert not data['read']['can']
    assert data['list']['can']
    assert not data['update']['can']
    assert not data['delete']['can']

    # Logged as system librarian
    #   * sys_lib can do everything about notification of its own organisation
    #   * sys_lib can't do anything about notification of other organisation
    login_user_via_session(client, system_librarian_martigny.user)
    res = client.get(notif_saxon_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert data['create']['can']
    assert data['update']['can']
    assert data['delete']['can']

    res = client.get(notif_sion_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert not data['read']['can']
    assert not data['update']['can']
    assert not data['delete']['can']


def test_notifcations_permissions(patron_martigny,
                                  librarian_martigny,
                                  system_librarian_martigny,
                                  org_martigny,
                                  notification_late_sion,
                                  notification_late_martigny,
                                  notification_late_saxon):
    """Test notifications permissions class."""

    # Anonymous user
    assert not NotificationPermission.list(None, {})
    assert not NotificationPermission.read(None, {})
    assert not NotificationPermission.create(None, {})
    assert not NotificationPermission.update(None, {})
    assert not NotificationPermission.delete(None, {})

    # As Patron
    notif_martigny = notification_late_martigny
    notif_saxon = notification_late_saxon
    notif_sion = notification_late_sion
    with mock.patch(
        'rero_ils.modules.notifications.permissions.current_patron',
        patron_martigny
    ):
        assert not NotificationPermission.list(None, notif_martigny)
        assert not NotificationPermission.read(None, notif_martigny)
        assert not NotificationPermission.create(None, notif_martigny)
        assert not NotificationPermission.update(None, notif_martigny)
        assert not NotificationPermission.delete(None, notif_martigny)

    # As Librarian
    with mock.patch(
        'rero_ils.modules.notifications.permissions.current_patron',
        librarian_martigny
    ), mock.patch(
        'rero_ils.modules.notifications.permissions.current_organisation',
        org_martigny
    ):
        assert NotificationPermission.list(None, notif_martigny)
        assert NotificationPermission.read(None, notif_martigny)
        assert NotificationPermission.create(None, notif_martigny)
        assert NotificationPermission.update(None, notif_martigny)
        assert NotificationPermission.delete(None, notif_martigny)

        assert NotificationPermission.read(None, notif_saxon)
        assert NotificationPermission.create(None, notif_saxon)
        assert NotificationPermission.update(None, notif_saxon)
        assert NotificationPermission.delete(None, notif_saxon)

        assert not NotificationPermission.read(None, notif_sion)
        assert not NotificationPermission.create(None, notif_sion)
        assert not NotificationPermission.update(None, notif_sion)
        assert not NotificationPermission.delete(None, notif_sion)

    # As System-librarian
    with mock.patch(
        'rero_ils.modules.notifications.permissions.current_patron',
        system_librarian_martigny
    ), mock.patch(
        'rero_ils.modules.notifications.permissions.current_organisation',
        org_martigny
    ):
        assert NotificationPermission.list(None, notif_saxon)
        assert NotificationPermission.read(None, notif_saxon)
        assert NotificationPermission.create(None, notif_saxon)
        assert NotificationPermission.update(None, notif_saxon)
        assert NotificationPermission.delete(None, notif_saxon)

        assert not NotificationPermission.read(None, notif_sion)
        assert not NotificationPermission.create(None, notif_sion)
        assert not NotificationPermission.update(None, notif_sion)
        assert not NotificationPermission.delete(None, notif_sion)
