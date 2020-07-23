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

from rero_ils.modules.vendors.permissions import VendorPermission


def test_vendor_permissions_api(client, org_sion, patron_martigny_no_email,
                                system_librarian_martigny_no_email,
                                vendor_martigny, vendor_sion):
    """Test organisations permissions api."""
    vendor_permissions_url = url_for(
        'api_blueprint.permissions',
        route_name='vendors'
    )
    vendor_martigny_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='vendors',
        record_pid=vendor_martigny.pid
    )
    vendor_sion_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='vendors',
        record_pid=vendor_sion.pid
    )

    # Not logged
    res = client.get(vendor_permissions_url)
    assert res.status_code == 401

    # Logged as patron
    login_user_via_session(client, patron_martigny_no_email.user)
    res = client.get(vendor_permissions_url)
    assert res.status_code == 403

    # Logged as system librarian
    #   * sys_lib can do everything about vendors of its own organisation
    #   * sys_lib can't do anything about vendors of other organisation
    login_user_via_session(client, system_librarian_martigny_no_email.user)
    res = client.get(vendor_martigny_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert data['create']['can']
    assert data['update']['can']
    assert data['delete']['can']

    res = client.get(vendor_sion_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert not data['read']['can']
    assert not data['update']['can']
    assert not data['delete']['can']


def test_vendor_permissions(patron_martigny_no_email,
                            librarian_martigny_no_email,
                            org_martigny, org_sion,
                            vendor_martigny, vendor_sion):
    """Test organisation permissions class."""

    # Anonymous user
    assert not VendorPermission.list(None, {})
    assert not VendorPermission.read(None, {})
    assert not VendorPermission.create(None, {})
    assert not VendorPermission.update(None, {})
    assert not VendorPermission.delete(None, {})

    # As Patron
    with mock.patch(
        'rero_ils.modules.vendors.permissions.current_patron',
        patron_martigny_no_email
    ):
        assert not VendorPermission.list(None, vendor_martigny)
        assert not VendorPermission.read(None, vendor_martigny)
        assert not VendorPermission.create(None, vendor_martigny)
        assert not VendorPermission.update(None, vendor_martigny)
        assert not VendorPermission.delete(None, vendor_martigny)

    # As Librarian
    with mock.patch(
        'rero_ils.modules.vendors.permissions.current_patron',
        librarian_martigny_no_email
    ), mock.patch(
        'rero_ils.modules.vendors.permissions.current_organisation',
        org_martigny
    ):
        assert VendorPermission.list(None, vendor_martigny)
        assert VendorPermission.read(None, vendor_martigny)
        assert VendorPermission.create(None, vendor_martigny)
        assert VendorPermission.update(None, vendor_martigny)
        assert VendorPermission.delete(None, vendor_martigny)

        assert not VendorPermission.create(None, vendor_sion)
        assert not VendorPermission.update(None, vendor_sion)
        assert not VendorPermission.delete(None, vendor_sion)
