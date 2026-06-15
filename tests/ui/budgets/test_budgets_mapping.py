# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Acquisition budget record mapping tests."""

from rero_ils.modules.acquisition.budgets.api import Budget, BudgetsSearch
from tests.utils import get_mapping


def test_budgets_search_mapping(search, db, org_martigny, budget_2017_martigny_data):
    """Test acquisition budget search index mapping."""
    search = BudgetsSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping
    budget = Budget.create(budget_2017_martigny_data, dbcommit=True, reindex=True, delete_pid=True)
    assert mapping == get_mapping(search.Meta.index)
    budget.delete(force=True, dbcommit=True, delindex=True)
