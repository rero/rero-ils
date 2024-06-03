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

"""Patron transaction event Record tests."""

from __future__ import absolute_import, print_function

from copy import deepcopy

import pytest
from jsonschema.exceptions import ValidationError

from rero_ils.modules.patron_transaction_events.api import PatronTransactionEvent
from rero_ils.modules.patron_transactions.api import (
    patron_transaction_id_fetcher as fetcher,
)


def test_patron_transaction_event_properties(
    patron_transaction_overdue_event_martigny, patron_transaction_overdue_martigny
):
    """Test patron transaction event properties."""
    pttr = patron_transaction_overdue_martigny
    ptre = patron_transaction_overdue_event_martigny
    events = PatronTransactionEvent.get_events_by_transaction_id(pttr.pid)
    assert ptre.pid in [hit.pid for hit in events]
    assert ptre.parent_pid == pttr.pid
    assert (
        PatronTransactionEvent.get_initial_amount_transaction_event(pttr.pid)
        == pttr.total_amount
    )


def test_patron_transaction_event_create(
    db, search_clear, patron_transaction_overdue_event_martigny
):
    """Test patron transaction event creation."""
    patron_event = deepcopy(patron_transaction_overdue_event_martigny)
    patron_event["type"] = "no_type"
    with pytest.raises(ValidationError):
        PatronTransactionEvent.create(patron_event, delete_pid=True)
    db.session.rollback()
    # Check amount is multiple of 0.01
    patron_event["type"] = "fee"
    patron_event["amount"] = 2.23333
    with pytest.raises(ValidationError) as err:
        PatronTransactionEvent.create(patron_event, delete_pid=True)
    assert "must be multiple of 0.01" in str(err)
    db.session.rollback()

    next_pid = PatronTransactionEvent.provider.identifier.next()
    patron_event["amount"] = 2.2
    record = PatronTransactionEvent.create(patron_event, delete_pid=True)
    next_pid += 1
    assert record == patron_event
    assert record.get("pid") == str(next_pid)
    assert record.get("amount") == 2.20

    pttr = PatronTransactionEvent.get_record_by_pid(str(next_pid))
    assert pttr == patron_event

    fetched_pid = fetcher(pttr.id, pttr)
    assert fetched_pid.pid_value == str(next_pid)
    assert fetched_pid.pid_type == "pttr"


def test_patron_transaction_event_can_delete(patron_transaction_overdue_event_martigny):
    """Test can delete."""
    can, reasons = patron_transaction_overdue_event_martigny.can_delete
    assert can
    assert reasons == {}
