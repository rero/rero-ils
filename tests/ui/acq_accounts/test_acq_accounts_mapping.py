# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Acquisition account Record mapping tests."""

from rero_ils.modules.acquisition.acq_accounts.api import AcqAccount, AcqAccountsSearch
from tests.utils import get_mapping


def test_acq_accounts_search_mapping(search, db, acq_account_fiction_martigny_data, budget_2020_martigny, lib_martigny):
    """Test acquisition account search index mapping."""
    search = AcqAccountsSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping
    account = AcqAccount.create(acq_account_fiction_martigny_data, dbcommit=True, reindex=True, delete_pid=True)
    assert mapping == get_mapping(search.Meta.index)
    account.delete(force=True, dbcommit=True, delindex=True)
