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

"""Patron transaction event record mapping tests."""
from utils import get_mapping

from rero_ils.modules.patron_transaction_events.api import (
    PatronTransactionEvent,
    PatronTransactionEventsSearch,
)


def test_patron_transaction_event_es_mapping(
    es, db, patron_transaction_overdue_event_martigny
):
    """Test patron_transaction event elasticsearch mapping."""
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
