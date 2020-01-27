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

"""API for manipulating patron transactions."""

from functools import partial

from .models import PatronTransactionIdentifier
from ..api import IlsRecord, IlsRecordsSearch
from ..fetchers import id_fetcher
from ..minters import id_minter
from ..providers import Provider

# provider
PatronTransactionProvider = type(
    'PatronTransactionProvider',
    (Provider,),
    dict(identifier=PatronTransactionIdentifier, pid_type='pttr')
)
# minter
patron_transaction_id_minter = partial(
    id_minter, provider=PatronTransactionProvider)
# fetcher
patron_transaction_id_fetcher = partial(
    id_fetcher, provider=PatronTransactionProvider)


class PatronTransactionsSearch(IlsRecordsSearch):
    """Patron Transactions Search."""

    class Meta:
        """Search only on patron transaction index."""

        index = 'patron_transactions'


class PatronTransaction(IlsRecord):
    """Patron Transaction class."""

    minter = patron_transaction_id_minter
    fetcher = patron_transaction_id_fetcher
    provider = PatronTransactionProvider
