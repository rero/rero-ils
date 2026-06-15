# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Patron transaction Record tests."""

from copy import deepcopy

import pytest

from rero_ils.modules.patron_transactions.api import (
    PatronTransaction,
)
from rero_ils.modules.patron_transactions.api import (
    patron_transaction_id_fetcher as fetcher,
)


def test_patron_transaction_properties(
    patron_transaction_overdue_martigny,
    patron_transaction_overdue_event_martigny,
    lib_martigny,
):
    """Test patron transaction properties."""
    pttr = patron_transaction_overdue_martigny
    assert pttr.notification_pid
    assert pttr.notification_transaction_library_pid == lib_martigny.pid
    assert pttr.get_number_of_patron_transaction_events() == 1


def test_patron_transaction_create(db, search_clear, patron_transaction_overdue_martigny, org_martigny):
    """Test patron transaction creation."""
    patron_transaction = deepcopy(patron_transaction_overdue_martigny)
    patron_transaction["status"] = "no_status"
    import jsonschema

    with pytest.raises(jsonschema.exceptions.ValidationError):
        PatronTransaction.create(patron_transaction, delete_pid=True)
    db.session.rollback()

    next_pid = PatronTransaction.provider.identifier.next()
    patron_transaction["status"] = "open"
    record = PatronTransaction.create(patron_transaction, delete_pid=True)
    next_pid += 1
    assert record == patron_transaction
    assert record.get("pid") == str(next_pid)

    pttr = PatronTransaction.get_record_by_pid(str(next_pid))
    assert pttr == patron_transaction

    fetched_pid = fetcher(pttr.id, pttr)
    assert fetched_pid.pid_value == str(next_pid)
    assert fetched_pid.pid_type == "pttr"

    can, reasons = patron_transaction_overdue_martigny.can_delete
    assert not can
    assert reasons["links"]["events"]

    assert patron_transaction_overdue_martigny.currency == org_martigny.get("default_currency")
