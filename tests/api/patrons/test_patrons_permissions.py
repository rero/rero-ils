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

from rero_ils.modules.patrons.permissions import PatronPermission


def test_patrons_permissions_api(client, patron_martigny_no_email,
                                 system_librarian_martigny_no_email,
                                 librarian_martigny_no_email,
                                 librarian_saxon_no_email,
                                 patron_sion_no_email):
    """Test patron permissions api."""
    patron_permissions_url = url_for(
        'api_blueprint.permissions',
        route_name='patrons'
    )
    patron_martigny_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='patrons',
        record_pid=patron_martigny_no_email.pid
    )
    patron_saxon_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='patrons',
        record_pid=librarian_saxon_no_email.pid
    )
    patron_sion_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='patrons',
        record_pid=patron_sion_no_email.pid
    )

    # Not logged
    res = client.get(patron_permissions_url)
    assert res.status_code == 401

    # Logged as patron
    login_user_via_session(client, patron_martigny_no_email.user)
    res = client.get(patron_permissions_url)
    assert res.status_code == 403

    # Logged as librarian
    #   * lib can 'list' and 'read' patron of its own organisation
    #   * lib can 'create', 'update', delete only for its library
    #   * lib can't 'read' patron of others organisation.
    #   * lib can't 'create', 'update', 'delete' patron for other org/lib
    login_user_via_session(client, librarian_martigny_no_email.user)
    res = client.get(patron_martigny_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert data['create']['can']
    assert data['update']['can']
    assert data['delete']['can']

    res = client.get(patron_saxon_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert not data['update']['can']
    assert not data['delete']['can']

    res = client.get(patron_sion_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert not data['read']['can']
    assert data['list']['can']
    assert not data['update']['can']
    assert not data['delete']['can']

    # Logged as system librarian
    #   * sys_lib can do everything about patron of its own organisation
    #   * sys_lib can't do anything about patron of other organisation
    login_user_via_session(client, system_librarian_martigny_no_email.user)
    res = client.get(patron_saxon_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert data['create']['can']
    assert data['update']['can']
    assert data['delete']['can']

    res = client.get(patron_sion_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert not data['read']['can']
    assert not data['update']['can']
    assert not data['delete']['can']


def test_patrons_permissions(patron_martigny_no_email,
                             librarian_martigny_no_email,
                             system_librarian_martigny_no_email,
                             org_martigny, librarian_saxon_no_email,
                             patron_sion_no_email):
    """Test patrons permissions class."""

    # Anonymous user
    assert not PatronPermission.list(None, {})
    assert not PatronPermission.read(None, {})
    assert not PatronPermission.create(None, {})
    assert not PatronPermission.update(None, {})
    assert not PatronPermission.delete(None, {})

    # As Patron
    sys_lib = system_librarian_martigny_no_email
    with mock.patch(
        'rero_ils.modules.patrons.permissions.current_patron',
        patron_martigny_no_email
    ):
        assert not PatronPermission.list(None, patron_martigny_no_email)
        assert not PatronPermission.read(None, patron_martigny_no_email)
        assert not PatronPermission.create(None, patron_martigny_no_email)
        assert not PatronPermission.update(None, patron_martigny_no_email)
        assert not PatronPermission.delete(None, patron_martigny_no_email)

    # As Librarian
    with mock.patch(
        'rero_ils.modules.patrons.permissions.current_patron',
        librarian_martigny_no_email
    ), mock.patch(
        'rero_ils.modules.patrons.permissions.current_organisation',
        org_martigny
    ):
        assert PatronPermission.list(None, patron_martigny_no_email)
        assert PatronPermission.read(None, patron_martigny_no_email)
        assert PatronPermission.create(None, patron_martigny_no_email)
        assert PatronPermission.update(None, patron_martigny_no_email)
        assert PatronPermission.delete(None, patron_martigny_no_email)

        assert PatronPermission.read(None, librarian_saxon_no_email)
        assert not PatronPermission.create(None, librarian_saxon_no_email)
        assert not PatronPermission.update(None, librarian_saxon_no_email)
        assert not PatronPermission.delete(None, librarian_saxon_no_email)

        assert not PatronPermission.read(None, patron_sion_no_email)
        assert not PatronPermission.create(None, patron_sion_no_email)
        assert not PatronPermission.update(None, patron_sion_no_email)
        assert not PatronPermission.delete(None, patron_sion_no_email)

        assert not PatronPermission.create(None, sys_lib)
        assert not PatronPermission.update(None, sys_lib)
        assert not PatronPermission.delete(None, sys_lib)

        assert not PatronPermission.delete(None, librarian_martigny_no_email)

    # As System-librarian
    with mock.patch(
        'rero_ils.modules.patrons.permissions.current_patron',
        system_librarian_martigny_no_email
    ), mock.patch(
        'rero_ils.modules.patrons.permissions.current_organisation',
        org_martigny
    ):
        assert PatronPermission.list(None, librarian_saxon_no_email)
        assert PatronPermission.read(None, librarian_saxon_no_email)
        assert PatronPermission.create(None, librarian_saxon_no_email)
        assert PatronPermission.update(None, librarian_saxon_no_email)
        assert PatronPermission.delete(None, librarian_saxon_no_email)

        assert not PatronPermission.read(None, patron_sion_no_email)
        assert not PatronPermission.create(None, patron_sion_no_email)
        assert not PatronPermission.update(None, patron_sion_no_email)
        assert not PatronPermission.delete(None, patron_sion_no_email)

        assert not PatronPermission.delete(None, sys_lib)
