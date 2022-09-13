# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
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

"""Budget API tests."""
from utils import flush_index

from rero_ils.modules.acquisition.acq_accounts.api import AcqAccountsSearch
from rero_ils.modules.acquisition.budgets.api import BudgetsSearch


def test_budget_properties(budget_2017_martigny):
    """Test budget properties."""
    assert budget_2017_martigny.name == budget_2017_martigny.get('name')


def test_budget_cascade_reindex(
    acq_account_fiction_martigny,
    budget_2020_martigny
):
    """Test budget cascading reindex."""
    budg = budget_2020_martigny
    acac = acq_account_fiction_martigny
    flush_index(BudgetsSearch.Meta.index)
    flush_index(AcqAccountsSearch.Meta.index)

    # when the `is_active` budget field change, the related account must be
    # reindex too.
    es_budg = BudgetsSearch().get_record_by_pid(budg.pid)
    es_acac = AcqAccountsSearch().get_record_by_pid(acac.pid)
    assert es_budg['is_active'] and es_acac['is_active']

    budg['is_active'] = False
    budg.update(budg, dbcommit=True, reindex=True)
    flush_index(BudgetsSearch.Meta.index)
    flush_index(AcqAccountsSearch.Meta.index)

    es_budg = BudgetsSearch().get_record_by_pid(budg.pid)
    es_acac = AcqAccountsSearch().get_record_by_pid(acac.pid)
    assert not es_budg['is_active'] and not es_acac['is_active']
