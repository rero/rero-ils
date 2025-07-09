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

"""Patron transaction Record mapping tests."""
from rero_ils.modules.patron_transactions.api import (
    PatronTransaction,
    PatronTransactionsSearch,
)
from tests.utils import get_mapping


def test_patron_transaction_es_mapping(search, db, patron_transaction_overdue_martigny):
    """Test patron_transaction elasticsearch mapping."""
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
