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

"""API for manipulating patron_transaction_events."""

from functools import partial

from .models import PatronTransactionEventIdentifier
from ..api import IlsRecord, IlsRecordsSearch
from ..fetchers import id_fetcher
from ..minters import id_minter
from ..providers import Provider

# provider
PatronTransactionEventProvider = type(
    'PatronTransactionEventProvider',
    (Provider,),
    dict(identifier=PatronTransactionEventIdentifier, pid_type='ptre')
)
# minter
patron_transaction_event_id_minter = partial(
    id_minter, provider=PatronTransactionEventProvider)
# fetcher
patron_transaction_event_id_fetcher = partial(
    id_fetcher, provider=PatronTransactionEventProvider)


class PatronTransactionEventsSearch(IlsRecordsSearch):
    """PatronTransactionEventsSearch."""

    class Meta:
        """Search only on patron_transaction_event index."""

        index = 'patron_transaction_events'


class PatronTransactionEvent(IlsRecord):
    """PatronTransactionEvent class."""

    minter = patron_transaction_event_id_minter
    fetcher = patron_transaction_event_id_fetcher
    provider = PatronTransactionEventProvider
