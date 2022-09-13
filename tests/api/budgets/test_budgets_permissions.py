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

import mock
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import get_json

from rero_ils.modules.acquisition.budgets.permissions import BudgetPermission


def test_budget_permissions_api(client, org_sion, patron_martigny,
                                system_librarian_martigny,
                                librarian_martigny,
                                budget_2017_martigny, budget_2020_sion):
    """Test budget permissions api."""
    budget_permissions_url = url_for(
        'api_blueprint.permissions',
        route_name='budgets'
    )
    budget_martigny_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='budgets',
        record_pid=budget_2017_martigny.pid
    )
    budget_sion_permission_url = url_for(
        'api_blueprint.permissions',
        route_name='budgets',
        record_pid=budget_2020_sion.pid
    )

    # Not logged
    res = client.get(budget_permissions_url)
    assert res.status_code == 401

    # Logged as patron
    login_user_via_session(client, patron_martigny.user)
    res = client.get(budget_permissions_url)
    assert res.status_code == 403

    # Logged as librarian
    #   * lib can 'list' and 'read' budget of its own organisation
    #   * lib can't 'create', 'update', delete any budgets
    #   * lib can't 'list' and 'read' budget of others organisation.
    login_user_via_session(client, librarian_martigny.user)
    res = client.get(budget_martigny_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert not data['create']['can']
    assert not data['update']['can']
    assert not data['delete']['can']

    res = client.get(budget_sion_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert not data['read']['can']
    assert data['list']['can']
    assert not data['create']['can']
    assert not data['update']['can']
    assert not data['delete']['can']

    # Logged as system librarian
    #   * sys_lib can do everything about budgets of its own organisation
    #   * sys_lib can't do anything about budgets of other organisation
    login_user_via_session(client, system_librarian_martigny.user)
    res = client.get(budget_martigny_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert data['read']['can']
    assert data['list']['can']
    assert not data['create']['can']
    assert not data['update']['can']
    assert not data['delete']['can']

    res = client.get(budget_sion_permission_url)
    assert res.status_code == 200
    data = get_json(res)
    assert not data['read']['can']
    assert not data['update']['can']
    assert not data['delete']['can']


def test_budget_permissions(patron_martigny,
                            librarian_martigny,
                            system_librarian_martigny,
                            org_martigny, org_sion,
                            budget_2018_martigny, budget_2020_sion):
    """Test budget permissions class."""

    # Anonymous user
    assert not BudgetPermission.list(None, {})
    assert not BudgetPermission.read(None, {})
    assert not BudgetPermission.create(None, {})
    assert not BudgetPermission.update(None, {})
    assert not BudgetPermission.delete(None, {})

    # As non Librarian
    assert not BudgetPermission.list(None, budget_2018_martigny)
    assert not BudgetPermission.read(None, budget_2018_martigny)
    assert not BudgetPermission.create(None, budget_2018_martigny)
    assert not BudgetPermission.update(None, budget_2018_martigny)
    assert not BudgetPermission.delete(None, budget_2018_martigny)

    # As Librarian
    with mock.patch(
        'rero_ils.modules.acquisition.budgets.permissions.current_librarian',
        librarian_martigny
    ):
        assert BudgetPermission.list(None, budget_2018_martigny)
        assert BudgetPermission.read(None, budget_2018_martigny)
        assert not BudgetPermission.create(None, budget_2018_martigny)
        assert not BudgetPermission.update(None, budget_2018_martigny)
        assert not BudgetPermission.delete(None, budget_2018_martigny)

        assert not BudgetPermission.read(None, budget_2020_sion)
        assert not BudgetPermission.create(None, budget_2020_sion)
        assert not BudgetPermission.update(None, budget_2020_sion)
        assert not BudgetPermission.delete(None, budget_2020_sion)

    # As System-librarian
    with mock.patch(
        'rero_ils.modules.acquisition.budgets.permissions.current_librarian',
        system_librarian_martigny
    ):
        assert BudgetPermission.list(None, budget_2018_martigny)
        assert BudgetPermission.read(None, budget_2018_martigny)
        assert not BudgetPermission.create(None, budget_2018_martigny)
        assert not BudgetPermission.update(None, budget_2018_martigny)
        assert not BudgetPermission.delete(None, budget_2018_martigny)

        assert not BudgetPermission.read(None, budget_2020_sion)
        assert not BudgetPermission.create(None, budget_2020_sion)
        assert not BudgetPermission.update(None, budget_2020_sion)
        assert not BudgetPermission.delete(None, budget_2020_sion)
