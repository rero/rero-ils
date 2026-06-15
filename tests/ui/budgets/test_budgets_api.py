# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Budget API tests."""

from rero_ils.modules.acquisition.acq_accounts.api import AcqAccountsSearch
from rero_ils.modules.acquisition.budgets.api import BudgetsSearch


def test_budget_properties(budget_2017_martigny):
    """Test budget properties."""
    assert budget_2017_martigny.name == budget_2017_martigny.get("name")


def test_budget_cascade_reindex(acq_account_fiction_martigny, budget_2020_martigny):
    """Test budget cascading reindex."""
    budg = budget_2020_martigny
    acac = acq_account_fiction_martigny
    BudgetsSearch.flush_and_refresh()
    AcqAccountsSearch.flush_and_refresh()

    # when the `is_active` budget field change, the related account must be
    # reindex too.
    search_budg = BudgetsSearch().get_record_by_pid(budg.pid)
    search_acac = AcqAccountsSearch().get_record_by_pid(acac.pid)
    assert search_budg["is_active"] and search_acac["is_active"]

    budg["is_active"] = False
    budg.update(budg, dbcommit=True, reindex=True)
    BudgetsSearch.flush_and_refresh()
    AcqAccountsSearch.flush_and_refresh()

    search_budg = BudgetsSearch().get_record_by_pid(budg.pid)
    search_acac = AcqAccountsSearch().get_record_by_pid(acac.pid)
    assert not search_budg["is_active"] and not search_acac["is_active"]
