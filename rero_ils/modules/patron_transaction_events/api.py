# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
# Copyright (C) 2019-2022 UCLouvain
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

from datetime import datetime, timezone
from functools import partial

from rero_ils.modules.api import IlsRecord, IlsRecordsIndexer, IlsRecordsSearch
from rero_ils.modules.extensions import DecimalAmountExtension
from rero_ils.modules.fetchers import id_fetcher
from rero_ils.modules.minters import id_minter
from rero_ils.modules.patron_transactions.models import PatronTransactionStatus
from rero_ils.modules.providers import Provider
from rero_ils.modules.utils import extracted_data_from_ref

from .models import PatronTransactionEventIdentifier, \
    PatronTransactionEventMetadata, PatronTransactionEventType

# provider
PatronTransactionEventProvider = type(
    'PatronTransactionEventProvider',
    (Provider,),
    dict(identifier=PatronTransactionEventIdentifier, pid_type='ptre')
)
# minter
patron_transaction_event_id_minter = partial(
    id_minter,
    provider=PatronTransactionEventProvider
)
# fetcher
patron_transaction_event_id_fetcher = partial(
    id_fetcher,
    provider=PatronTransactionEventProvider
)


class PatronTransactionEventsSearch(IlsRecordsSearch):
    """PatronTransactionEventsSearch."""

    class Meta:
        """Search only on patron_transaction_event index."""

        index = 'patron_transaction_events'
        doc_types = None
        fields = ('*', )
        facets = {}

        default_filter = None


class PatronTransactionEvent(IlsRecord):
    """PatronTransactionEvent class."""

    minter = patron_transaction_event_id_minter
    fetcher = patron_transaction_event_id_fetcher
    provider = PatronTransactionEventProvider
    model_cls = PatronTransactionEventMetadata
    pids_exist_check = {
        'required': {
            'pttr': 'parent'
        },
        'not_required': {
            'lib': 'library',
            'ptrn': 'operator'
        }
    }

    _extensions = [
        DecimalAmountExtension('amount')
    ]

    @classmethod
    def create(cls, data, id_=None, delete_pid=False,
               dbcommit=False, reindex=False, update_parent=True, **kwargs):
        """Create patron transaction event record."""
        if 'creation_date' not in data:
            data['creation_date'] = datetime.now(timezone.utc).isoformat()
        record = super().create(
            data, id_, delete_pid, dbcommit, reindex, **kwargs)
        if update_parent and record:
            record.update_parent_patron_transaction()
        return record

    # TODO: do we have to set dbcommit and reindex to True so the
    # of the rest api for create and update works properly ?
    # For PatronTransaction we have to set it to True for the tests.
    def update(self, data, commit=True, dbcommit=True, reindex=True):
        """Update data for record."""
        return super().update(
            data=data,
            commit=commit,
            dbcommit=dbcommit,
            reindex=reindex
        )

    def update_parent_patron_transaction(self):
        """Update parent patron transaction amount and status."""
        # NOTE :
        #   due to bit representation of float number
        #   (https://en.wikipedia.org/wiki/IEEE_754), the arithmetic operation
        #   with float can cause some strange behavior
        #     >>> 10 - 9.54
        #     0.46000000000000085
        #   To solve this problem in our case, as we keep only 2 decimal
        #   digits, we can multiply amounts by 100, cast result as integer,
        #   do operation with these values, and (at the end) divide the result
        #   by 100.
        if not self.amount or \
           self.event_type == PatronTransactionEventType.DISPUTE:
            return

        pttr = self.patron_transaction
        total_amount = int(pttr.get('total_amount') * 100)
        amount = int(self.amount * 100)
        if self.event_type == PatronTransactionEventType.FEE:
            total_amount += amount
        else:
            total_amount -= amount
        pttr['total_amount'] = total_amount / 100
        if total_amount == 0:
            pttr['status'] = PatronTransactionStatus.CLOSED
        pttr.update(pttr, dbcommit=True, reindex=True)

    @classmethod
    def get_events_by_transaction_id(cls, transaction_pid):
        """Return events of current transaction.

        :param transaction_pid: The transaction PID
        :return: Array of events selected by transaction PID
        """
        return PatronTransactionEventsSearch()\
            .params(preserve_order=True)\
            .filter('term', parent__pid=transaction_pid)\
            .sort({'creation_date': {'order': 'desc'}})\
            .scan()

    @classmethod
    def get_initial_amount_transaction_event(cls, transaction_pid):
        """Get initial amount by transaction.

        :param transaction_pid: The transaction PID
        :return: The initial amount for selected transaction
        """
        result = PatronTransactionEventsSearch()\
            .params(preserve_order=True)\
            .filter('term', parent__pid=transaction_pid)\
            .sort({'creation_date': {'order': 'asc'}})\
            .source(['amount'])\
            .scan()
        return next(result).amount

    @property
    def parent_pid(self):
        """Return the parent pid of the patron transaction event."""
        return extracted_data_from_ref(self.get('parent'))

    @property
    def patron_transaction(self):
        """Return the parent patron transaction of the event."""
        return extracted_data_from_ref(self.get('parent'), data='record')

    @property
    def event_type(self):
        """Return the type of the patron transaction event."""
        return self.get('type')

    @property
    def amount(self):
        """Return the amount of the patron transaction event."""
        return self.get('amount')

    @property
    def patron_pid(self):
        """Return the patron pid of the patron transaction event."""
        if parent := self.patron_transaction:
            return parent.patron_pid

    @property
    def organisation_pid(self):
        """Return the organisation pid of the patron transaction event."""
        if parent := self.patron_transaction:
            return parent.organisation_pid


class PatronTransactionEventsIndexer(IlsRecordsIndexer):
    """Holdings indexing class."""

    record_cls = PatronTransactionEvent

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(record_id_iterator, doc_type='ptre')
