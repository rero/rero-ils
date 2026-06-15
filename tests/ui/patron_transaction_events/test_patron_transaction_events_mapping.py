# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Patron transaction event record mapping tests."""

from rero_ils.modules.patron_transaction_events.api import (
    PatronTransactionEvent,
    PatronTransactionEventsSearch,
)
from tests.utils import get_mapping


def test_patron_transaction_event_search_mapping(es, db, patron_transaction_overdue_event_martigny):
    """Test patron_transaction event search index mapping."""
    search = PatronTransactionEventsSearch()
    mapping = get_mapping(search.Meta.index)
    assert mapping
    ptre = PatronTransactionEvent.create(
        patron_transaction_overdue_event_martigny,
        dbcommit=True,
        reindex=True,
        delete_pid=True,
    )
    assert mapping == get_mapping(search.Meta.index)
    ptre.delete(force=True, dbcommit=True, delindex=True)
