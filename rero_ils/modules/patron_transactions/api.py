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

"""API for manipulating patron transactions."""

from functools import partial

from werkzeug.utils import cached_property

from rero_ils.modules.api import IlsRecord, IlsRecordsIndexer, IlsRecordsSearch
from rero_ils.modules.fetchers import id_fetcher
from rero_ils.modules.minters import id_minter
from rero_ils.modules.organisations.api import Organisation
from rero_ils.modules.patron_transaction_events.api import \
    PatronTransactionEvent, PatronTransactionEventsSearch
from rero_ils.modules.providers import Provider
from rero_ils.modules.utils import extracted_data_from_ref, sorted_pids

from .extensions import PatronTransactionExtension
from .models import PatronTransactionIdentifier, PatronTransactionMetadata

# provider
PatronTransactionProvider = type(
    'PatronTransactionProvider',
    (Provider,),
    dict(identifier=PatronTransactionIdentifier, pid_type='pttr')
)
# minter
patron_transaction_id_minter = partial(
    id_minter,
    provider=PatronTransactionProvider
)
# fetcher
patron_transaction_id_fetcher = partial(
    id_fetcher,
    provider=PatronTransactionProvider
)


class PatronTransactionsSearch(IlsRecordsSearch):
    """Patron Transactions Search."""

    class Meta:
        """Search only on patron transaction index."""

        index = 'patron_transactions'
        doc_types = None
        fields = ('*', )
        facets = {}

        default_filter = None


class PatronTransaction(IlsRecord):
    """Patron Transaction class."""

    _extensions = [
        PatronTransactionExtension()
    ]

    minter = patron_transaction_id_minter
    fetcher = patron_transaction_id_fetcher
    provider = PatronTransactionProvider
    model_cls = PatronTransactionMetadata
    pids_exist_check = {
        'required': {
            'ptrn': 'patron'
        },
        'not_required': {
            'org': 'organisation',
            'notif': 'notification'
        }
    }

    def __init__(self, data, model=None, **kwargs):
        """Initialize a patron transaction object."""
        self.event_pids = []
        super().__init__(data, model, **kwargs)

    # API METHODS =============================================================
    #   Overriding the `IlsRecord` default behavior for create and update
    #   Invenio API methods.

    # TODO: do we have to set dbcomit and reindex to True so the
    #       of the rest api for create and update works properly ?
    #       For PatronTransaction we have to set it to True for the tests.
    def update(self, data, commit=True, dbcommit=True, reindex=True):
        """Update data for record."""
        return super().update(
            data=data,
            commit=commit,
            dbcommit=dbcommit,
            reindex=reindex
        )

    # GETTER & SETTER =========================================================
    #   * Define some properties as shortcut to quickly access object attrs.
    #   * Defines some getter methods to access specific object values.

    @property
    def loan_pid(self):
        """Get the `Loan` pid related to this transaction."""
        if self.get('loan'):
            return extracted_data_from_ref(self['loan'])

    @cached_property
    def loan(self):
        """Get the `Loan` record related to this transaction."""
        if self.get('loan'):
            return extracted_data_from_ref(self['loan'], data='record')

    @property
    def document_pid(self):
        """Get the `Document` pid related to this transaction."""
        if loan := self.loan:
            return loan.document_pid

    @property
    def item_pid(self):
        """Get the `Item` pid related to this transaction."""
        if loan := self.loan:
            return loan.item_pid

    @property
    def library_pid(self):
        """Get the `Library` pid related to this transaction."""
        if loan := self.loan:
            return loan.library_pid

    @property
    def patron_pid(self):
        """Get the `Patron` pid related to this transaction."""
        return extracted_data_from_ref(self.get('patron'))

    @property
    def patron(self):
        """Get the `Patron` pid related to this transaction."""
        return extracted_data_from_ref(self.get('patron'), data='record')

    @property
    def total_amount(self):
        """Shortcut to get the transaction total_amount of the transaction."""
        return self.get('total_amount')

    @property
    def notification_pid(self):
        """Get the `Notification` pid related to this transaction."""
        if self.get('notification'):
            return extracted_data_from_ref(self.get('notification'))

    @cached_property
    def notification(self):
        """Get the `Notification` record related to this transaction."""
        if self.get('notification'):
            return extracted_data_from_ref(
                self.get('notification'), data='record')

    @property
    def notification_transaction_library_pid(self):
        """Return the transaction library of the notification."""
        if notif := self.notification:
            if location := notif.transaction_location:
                return location.library_pid

    @property
    def notification_transaction_user_pid(self):
        """Return the transaction user pid of the notification."""
        if notif := self.notification:
            return notif.transaction_user_pid

    @property
    def status(self):
        """Return the status of the patron transaction."""
        return self.get('status')

    @property
    def currency(self):
        """Return patron transaction currency."""
        return Organisation\
            .get_record_by_pid(self.organisation_pid)\
            .get('default_currency')

    @property
    def events(self):
        """Shortcut for events of the patron transaction."""
        query = PatronTransactionEventsSearch()\
            .filter('term', parent__pid=self.pid)\
            .source(False)
        for hit in query.scan():
            yield PatronTransactionEvent.get_record(hit.meta.id)

    def get_number_of_patron_transaction_events(self):
        """Get number of patron transaction events."""
        return PatronTransactionEventsSearch()\
            .filter('term', parent__pid=self.pid)\
            .count()

    def get_links_to_me(self, get_pids=False):
        """Get the links between this record and other records.

        :param get_pids: if True, return list of linked pids, otherwise return
               count of linked records
        """
        links = {}
        query = PatronTransactionEventsSearch() \
            .filter('term', parent__pid=self.pid)
        events = sorted_pids(query) if get_pids else query.count()
        if events:
            links['events'] = events
        return links

    def reasons_not_to_delete(self):
        """Get reasons not to delete record."""
        reasons = {}
        if links := self.get_links_to_me():
            reasons['links'] = links
        return reasons


class PatronTransactionsIndexer(IlsRecordsIndexer):
    """Holdings indexing class."""

    record_cls = PatronTransaction

    def index(self, record):
        """Indexing a record."""
        # Indexing of events created in the extension
        for pid in record.event_pids:
            if event := PatronTransactionEvent.get_record_by_pid(pid):
                event.reindex()
        return super().index(record)

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(record_id_iterator, doc_type='pttr')
