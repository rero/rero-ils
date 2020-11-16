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

from rero_ils.modules.ill_requests.permissions import ILLRequestPermission


def test_ill_requests_permissions_api(client, librarian_martigny_no_email,
                                      ill_request_martigny, ill_request_sion):
    """Test ill_request permissions api."""
    illr_permissions_url = url_for(
        'api_blueprint.permissions',
        route_name='ill_requests'
    )
    illr_martigny_permissions_url = url_for(
        'api_blueprint.permissions',
        route_name='ill_requests',
        record_pid=ill_request_martigny.pid
    )
    illr_sion_permissions_url = url_for(
        'api_blueprint.permissions',
        route_name='ill_requests',
        record_pid=ill_request_sion.pid
    )

    # Not logged
    res = client.get(illr_permissions_url)
    assert res.status_code == 401

    # Logged as librarian
    #   * lib can 'list', 'create' ill_requests
    #   * lib can 'read', 'update', 'delete' ill_request from its own
    #     organisation
    login_user_via_session(client, librarian_martigny_no_email.user)
    res = client.get(illr_martigny_permissions_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['list']['can']
    assert data['read']['can']
    assert data['create']['can']
    assert data['update']['can']
    assert not data['delete']['can']
    res = client.get(illr_sion_permissions_url)
    data = get_json(res)
    assert not data['read']['can']
    assert not data['update']['can']
    assert not data['delete']['can']


def test_ill_requests_permissions(patron_martigny_no_email,
                                  librarian_martigny_no_email,
                                  system_librarian_martigny_no_email,
                                  ill_request_martigny, ill_request_sion,
                                  org_martigny):
    """Test patron types permissions class."""

    # Anonymous user
    assert not ILLRequestPermission.list(None, {})
    assert not ILLRequestPermission.read(None, {})
    assert not ILLRequestPermission.create(None, {})
    assert not ILLRequestPermission.update(None, {})
    assert not ILLRequestPermission.delete(None, {})

    # As Patron
    with mock.patch(
        'rero_ils.modules.ill_requests.permissions.current_patron',
        patron_martigny_no_email
    ), mock.patch(
        'rero_ils.modules.ill_requests.permissions.current_organisation',
        org_martigny
    ):
        assert ILLRequestPermission.list(None, ill_request_martigny)
        assert ILLRequestPermission.read(None, ill_request_martigny)
        assert ILLRequestPermission.create(None, ill_request_martigny)
        assert not ILLRequestPermission.update(None, ill_request_martigny)
        assert not ILLRequestPermission.delete(None, ill_request_martigny)

        assert ILLRequestPermission.list(None, ill_request_sion)
        assert not ILLRequestPermission.read(None, ill_request_sion)
        assert ILLRequestPermission.create(None, ill_request_sion)
        assert not ILLRequestPermission.update(None, ill_request_sion)
        assert not ILLRequestPermission.delete(None, ill_request_sion)

    # As Librarian
    with mock.patch(
        'rero_ils.modules.ill_requests.permissions.current_patron',
        librarian_martigny_no_email
    ), mock.patch(
        'rero_ils.modules.ill_requests.permissions.current_organisation',
        org_martigny
    ):
        assert ILLRequestPermission.list(None, ill_request_martigny)
        assert ILLRequestPermission.read(None, ill_request_martigny)
        assert ILLRequestPermission.create(None, ill_request_martigny)
        assert ILLRequestPermission.update(None, ill_request_martigny)
        assert not ILLRequestPermission.delete(None, ill_request_martigny)

        assert ILLRequestPermission.list(None, ill_request_sion)
        assert not ILLRequestPermission.read(None, ill_request_sion)
        assert ILLRequestPermission.create(None, ill_request_sion)
        assert not ILLRequestPermission.update(None, ill_request_sion)
        assert not ILLRequestPermission.delete(None, ill_request_sion)

    # As System-librarian
    with mock.patch(
        'rero_ils.modules.ill_requests.permissions.current_patron',
        system_librarian_martigny_no_email
    ), mock.patch(
        'rero_ils.modules.ill_requests.permissions.current_organisation',
        org_martigny
    ):
        assert ILLRequestPermission.list(None, ill_request_martigny)
        assert ILLRequestPermission.read(None, ill_request_martigny)
        assert ILLRequestPermission.create(None, ill_request_martigny)
        assert ILLRequestPermission.update(None, ill_request_martigny)
        assert not ILLRequestPermission.delete(None, ill_request_martigny)
