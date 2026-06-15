# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Patron transaction Record mapping tests."""

from rero_ils.modules.patron_transactions.api import (
    PatronTransaction,
    PatronTransactionsSearch,
)
from tests.utils import get_mapping


def test_patron_transaction_search_mapping(search, db, patron_transaction_overdue_martigny):
    """Test patron_transaction search index mapping."""
    search = PatronTransactionsSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping
    pttr = PatronTransaction.create(
        patron_transaction_overdue_martigny,
        dbcommit=True,
        reindex=True,
        delete_pid=True,
    )
    assert mapping == get_mapping(search.Meta.index)
    for event in pttr.events:
        event.delete(force=True, dbcommit=True, delindex=True)
    pttr.delete(force=True, dbcommit=True, delindex=True)
