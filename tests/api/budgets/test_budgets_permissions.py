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
from utils import check_permission

from rero_ils.modules.acquisition.budgets.permissions import \
    BudgetPermissionPolicy


def test_budget_permissions(
    patron_martigny, librarian_martigny,
    budget_2018_martigny, budget_2020_sion
):
    """Test budget permissions class."""

    # Anonymous user
    identity_changed.send(
        current_app._get_current_object(), identity=AnonymousIdentity()
    )
    check_permission(BudgetPermissionPolicy, {
        'search': False,
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, {})

    # Patron :: can't operate any operation about Budget
    login_user(patron_martigny.user)
    check_permission(BudgetPermissionPolicy, {
        'search': False,
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, budget_2018_martigny)

    # Staff members :: can only search and read (only org record)
    login_user(librarian_martigny.user)
    check_permission(BudgetPermissionPolicy, {
        'search': True,
        'read': True,
        'create': False,
        'update': False,
        'delete': False
    }, budget_2018_martigny)
    check_permission(BudgetPermissionPolicy, {
        'search': True,
        'read': False,
        'create': False,
        'update': False,
        'delete': False
    }, budget_2020_sion)
