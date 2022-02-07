# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2022 RERO
# Copyright (C) 2022 UCLouvain
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

from .models import PatronTransactionIdentifier, PatronTransactionMetadata
from ..api import IlsRecord, IlsRecordsIndexer, IlsRecordsSearch
from ..fetchers import id_fetcher
from ..minters import id_minter
from ..organisations.api import Organisation
from ..patron_transaction_events.api import PatronTransactionEvent, \
    PatronTransactionEventsSearch
from ..providers import Provider
from ..utils import extracted_data_from_ref, sorted_pids

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
        doc_types = None
        fields = ('*', )
        facets = {}

        default_filter = None


class PatronTransaction(IlsRecord):
    """Patron Transaction class."""

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

    # API METHODS =============================================================
    #   Overriding the `IlsRecord` default behavior for create and update
    #   Invenio API methods.

    @classmethod
    def create(cls, data, id_=None, delete_pid=False,
               dbcommit=False, reindex=False, steps=None, **kwargs):
        """Create patron transaction record."""
        # create the record
        record = super().create(
            data, id_, delete_pid, dbcommit, reindex, **kwargs)
        PatronTransactionEvent.create_event_from_patron_transaction(
            patron_transaction=record,
            steps=steps,
            dbcommit=dbcommit,
            reindex=reindex,
            delete_pid=delete_pid,
            update_parent=False
        )
        return record

    # TODO: do we have to set dbcomit and reindex to True so the
    #       of the rest api for create and update works properly ?
    #       For PatronTransaction we have to set it to True for the tests.
    def update(self, data, commit=True, dbcommit=True, reindex=True):
        """Update data for record."""
        return super().update(
            data=data, commit=commit, dbcommit=dbcommit, reindex=reindex)

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
        from ..loans.api import Loan
        pid = self.loan_pid
        if pid:
            return Loan.get_record_by_pid(pid)

    @property
    def document_pid(self):
        """Get the `Document` pid related to this transaction."""
        loan = self.loan
        if loan:
            return loan.document_pid

    @property
    def library_pid(self):
        """Get the `Library` pid related to this transaction."""
        loan = self.loan
        if loan:
            return loan.library_pid

    @property
    def patron_pid(self):
        """Get the `Patron` pid related to this transaction."""
        return extracted_data_from_ref(self.get('patron'))

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
        from ..notifications.api import Notification
        pid = self.notification_pid
        if pid:
            return Notification.get_record_by_pid(pid)

    @property
    def notification_transaction_library_pid(self):
        """Return the transaction library of the notification."""
        notif = self.notification
        if notif:
            location = notif.transaction_location
            if location:
                return location.library_pid

    @property
    def notification_transaction_user_pid(self):
        """Return the transaction user pid of the notification."""
        notif = self.notification
        if notif:
            return notif.transaction_user_pid

    @property
    def status(self):
        """Return the status of the patron transaction."""
        return self.get('status')

    @property
    def currency(self):
        """Return patron transaction currency."""
        organisation_pid = self.organisation_pid
        return Organisation.get_record_by_pid(organisation_pid).get(
            'default_currency')

    @property
    def events(self):
        """Shortcut for events of the patron transaction."""
        query = PatronTransactionEventsSearch()\
            .filter('term', parent__pid=self.pid)\
            .source('pid')
        for result in query.scan():
            yield PatronTransactionEvent.get_record_by_pid(result.pid)

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
        links = self.get_links_to_me()
        if links:
            reasons['links'] = links
        return reasons


class PatronTransactionsIndexer(IlsRecordsIndexer):
    """Holdings indexing class."""

    record_cls = PatronTransaction

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(record_id_iterator, doc_type='pttr')
