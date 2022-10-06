# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2022 RERO
# Copyright (C) 2022 UCLouvain
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

from flask import current_app
from flask_principal import AnonymousIdentity, identity_changed
from flask_security import login_user
from mock import mock
from utils import check_permission

from rero_ils.modules.acquisition.acq_accounts.permissions import \
    AcqAccountPermissionPolicy


def test_acq_accounts_permissions(patron_martigny,
                                  librarian_martigny, librarian2_martigny,
                                  system_librarian_martigny,
                                  org_martigny, org_sion, lib_sion,
                                  acq_account_fiction_martigny,
                                  acq_account_books_saxon,
                                  acq_account_fiction_sion):
    """Test acq_account permissions class."""

    # Anonymous user & Patron :: None action allowed
    identity_changed.send(
        current_app._get_current_object(), identity=AnonymousIdentity()
    )
    check_permission(AcqAccountPermissionPolicy, {
        'search': False,
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, {})
    login_user(patron_martigny.user)
    check_permission(AcqAccountPermissionPolicy, {
        'search': False,
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, acq_account_fiction_martigny)

    # As staff member without any specific access :
    #   - None action allowed
    #   - except read record of its own library (pro_read_only)
    login_user(librarian2_martigny.user)
    check_permission(AcqAccountPermissionPolicy, {
        'search': True,
        'read': True,
        'create': False,
        'update': False,
        'delete': False
    }, acq_account_fiction_martigny)
    check_permission(AcqAccountPermissionPolicy, {
        'search': True,
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, acq_account_fiction_sion)

    # As staff member with "library-administration" role :
    #   - Search :: everything
    #   - Read :: record of its own library
    #   - Create/Update/Delete :: record of its own library
    login_user(librarian_martigny.user)
    check_permission(AcqAccountPermissionPolicy, {
        'search': True,
        'read': True,
        'create': True,
        'update': True,
        'delete': True
    }, acq_account_fiction_martigny)
    check_permission(AcqAccountPermissionPolicy, {
        'search': True,
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, acq_account_books_saxon)

    # As staff member with "full_permissions" role :
    #   - Search :: everything
    #   - Read :: record of its own organisation
    #   - Create/Update/Delete :: record of its own organisation
    login_user(system_librarian_martigny.user)
    check_permission(AcqAccountPermissionPolicy, {
        'search': True,
        'read': True,
        'create': True,
        'update': True,
        'delete': True
    }, acq_account_books_saxon)

    # Special case !!! An acquisition account linked to a closed budget
    # should be considerate as roll-overed and can't be updated.
    with mock.patch(
        'rero_ils.modules.acquisition.acq_accounts.api.AcqAccount.is_active',
        False
    ):
        check_permission(AcqAccountPermissionPolicy, {
            'search': True,
            'read': True,
            'create': False,
            'update': False,
            'delete': False
        }, acq_account_fiction_martigny)
