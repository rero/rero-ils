# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
# Copyright (C) 2020 UCLouvain
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

from datetime import datetime, timezone
from functools import partial

from flask_babelex import gettext as _

from .models import PatronTransactionIdentifier, PatronTransactionMetadata
from ..api import IlsRecord, IlsRecordsIndexer, IlsRecordsSearch
from ..fetchers import id_fetcher
from ..minters import id_minter
from ..organisations.api import Organisation
from ..patron_transaction_events.api import PatronTransactionEvent, \
    PatronTransactionEventsSearch
from ..providers import Provider
from ..utils import extracted_data_from_ref, get_ref_for_pid, sorted_pids

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

    @classmethod
    def _build_transaction_query(cls, patron_pid, status=None, types=None):
        """Private function to build a transaction query linked to a patron.

        :param patron_pid: the patron pid being searched
        :param status: (optional) array of transaction status filter,
        :param types: (optional) array of transaction types filter,
        :return: return prepared query.
        """
        query = PatronTransactionsSearch() \
            .filter('term', patron__pid=patron_pid)
        if status:
            query = query.filter('term', status=status)
        if types:
            query = query.filter('terms', type=types)
        return query

    @classmethod
    def get_transactions_pids_for_patron(cls, patron_pid, status=None):
        """Get patron transactions linked to a patron.

        :param patron_pid: the patron pid being searched
        :param status: (optional) transaction status filter,
        """
        query = cls._build_transaction_query(patron_pid, status)
        results = query.source('pid').scan()
        for result in results:
            yield result.pid

    @classmethod
    def get_transactions_total_amount_for_patron(cls, patron_pid, status=None,
                                                 types=None,
                                                 with_subscription=True):
        """Get total amount transactions linked to a patron.

        :param patron_pid: the patron pid being searched
        :param status: (optional) transaction status filter,
        :param types: (optional) transaction type filter,
        :param with_subscription: (optional) include or exclude subscription
        type filter.
        :return: return total amount of transactions.
        """
        search = cls._build_transaction_query(patron_pid, status, types)
        if not with_subscription:
            search = search.exclude('terms', type=['subscription'])
        search.aggs.metric('transactions_total_amount',
                           'sum', field='total_amount')
        # set the from/size to 0
        search = search[0:0]
        results = search.execute()
        return results.aggregations.transactions_total_amount.value

    @classmethod
    def get_transactions_count_for_patron(cls, patron_pid, status=None):
        """Get patron transactions count linked to a patron.

        :param patron_pid: the patron pid being searched
        :param status: (optional) transaction status filter,
        """
        query = cls._build_transaction_query(patron_pid, status)
        return query.source().count()

    @classmethod
    def get_transactions_pids_for_patron(cls, patron_pid, status=None):
        """Get patron transactions pids linked to a patron.

        :param patron_pid: the patron pid being searched
        :param status: (optional) transaction status filter,
        """
        query = cls._build_transaction_query(patron_pid, status)
        return sorted_pids(query)

    @classmethod
    def get_transactions_by_patron_pid(cls, patron_pid, status=None):
        """Return opened fees for patron.

        :param patron_pid: the patron PID
        :param status: the status of transaction
        :return: return an array of transaction
        """
        query = cls._build_transaction_query(patron_pid, status)
        return query\
            .params(preserve_order=True)\
            .sort({'creation_date': {'order': 'asc'}})\
            .scan()

    @classmethod
    def get_last_transaction_by_loan_pid(cls, loan_pid, status=None):
        """Return last fee for loan.

        :param loan_pid: the loan PID
        :param status: the status of transaction
        :return: return last transaction transaction
        """
        query = PatronTransactionsSearch() \
            .filter('term', loan__pid=loan_pid)
        if status:
            query = query.filter('term', status=status)
        results = query\
            .sort({'creation_date': {'order': 'desc'}})\
            .source('pid').scan()
        try:
            pid = next(results).pid
            return PatronTransaction.get_record_by_pid(pid)
        except StopIteration:
            pass

    @property
    def document_pid(self):
        """Return the document pid of the the patron transaction."""
        return self.loan.document_pid if self.loan else None

    @property
    def library_pid(self):
        """Return the library pid of the the patron transaction."""
        return self.loan.library_pid if self.loan else None

    @property
    def patron_pid(self):
        """Return the patron pid of the patron transaction."""
        return extracted_data_from_ref(self.get('patron'))

    @property
    def total_amount(self):
        """Return the total_amount of the patron transaction."""
        return self.get('total_amount')

    @property
    def loan_pid(self):
        """Return the loan pid linked to the patron transaction."""
        if self.get('loan'):
            return extracted_data_from_ref(self['loan'])

    @property
    def loan(self):
        """Return the `Loan` linked to the patron transaction."""
        from ..loans.api import Loan
        pid = self.loan_pid
        if pid:
            return Loan.get_record_by_pid(pid)

    @property
    def notification_pid(self):
        """Return the notification pid of the patron transaction."""
        if self.get('notification'):
            return extracted_data_from_ref(self.get('notification'))

    @property
    def notification(self):
        """Return the notification of the patron transaction."""
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

    @classmethod
    def create_patron_transaction_from_overdue_loan(
            cls, loan, dbcommit=True, reindex=True, delete_pid=False):
        """Create a patron transaction for an overdue loan."""
        from ..loans.utils import sum_for_fees
        fees = loan.get_overdue_fees
        total_amount = sum_for_fees(fees)
        if total_amount > 0:
            data = {
                'loan': {
                    '$ref': get_ref_for_pid('loans', loan.pid)
                },
                'patron': {
                    '$ref': get_ref_for_pid('ptrn', loan.patron_pid)
                },
                'organisation': {
                    '$ref': get_ref_for_pid('org', loan.organisation_pid)
                },
                'type': 'overdue',
                'status': 'open',
                'note': 'incremental overdue fees',
                'total_amount': total_amount,
                'creation_date': datetime.now(timezone.utc).isoformat(),
            }
            steps = [
                {'timestamp': fee[1].isoformat(), 'amount': fee[0]}
                for fee in fees
            ]
            return cls.create(
                data,
                dbcommit=dbcommit,
                reindex=reindex,
                delete_pid=delete_pid,
                steps=steps
            )

    @classmethod
    def create_patron_transaction_from_notification(
            cls, notification=None, dbcommit=None, reindex=None,
            delete_pid=None):
        """Create a patron transaction from notification."""
        from ..notifications.utils import calculate_notification_amount
        total_amount = calculate_notification_amount(notification)
        if total_amount > 0:  # no need to create transaction if amount <= 0 !
            data = {
                'notification': {
                    '$ref': get_ref_for_pid('notif', notification.pid)
                },
                'loan': {
                    '$ref': get_ref_for_pid('loans', notification.loan_pid)
                },
                'patron': {
                    '$ref': get_ref_for_pid('ptrn', notification.patron_pid)
                },
                'organisation': {
                    '$ref': get_ref_for_pid(
                        'org',
                        notification.organisation_pid
                    )
                },
                'total_amount': total_amount,
                'creation_date': datetime.now(timezone.utc).isoformat(),
                'type': 'overdue',
                'status': 'open'
            }
            return cls.create(
                data,
                dbcommit=dbcommit,
                reindex=reindex,
                delete_pid=delete_pid
            )

    @classmethod
    def create_subscription_for_patron(cls, patron, patron_type, start_date,
                                       end_date, dbcommit=None, reindex=None,
                                       delete_pid=None):
        """Create a subscription patron transaction for a patron.

        :param patron: the patron linked to the subscription
        :param patron_type: the patron_type for which we need to create the
                            subscription
        :param start_date: As `datetime`, the starting date of the subscription
        :param end_date: As `datetime`, the ending date of the subscription
        """
        record = {}
        if patron_type.is_subscription_required:
            data = {
                'patron': {
                    '$ref': get_ref_for_pid('ptrn', patron.pid)
                },
                'organisation': {
                    '$ref': get_ref_for_pid('org', patron.organisation_pid)
                },
                'total_amount': patron_type.get('subscription_amount'),
                'creation_date': datetime.now(timezone.utc).isoformat(),
                'type': 'subscription',
                'status': 'open',
                'note': _("Subscription for '{name}' from {start} to {end}")
                        .format(
                            name=patron_type.get('name'),
                            start=start_date.strftime('%Y-%m-%d'),
                            end=end_date.strftime('%Y-%m-%d')
                        )
            }
            record = cls.create(
                data,
                dbcommit=dbcommit,
                reindex=reindex,
                delete_pid=delete_pid
            )
        return record

    @property
    def currency(self):
        """Return patron transaction currency."""
        organisation_pid = self.organisation_pid
        return Organisation.get_record_by_pid(organisation_pid).get(
            'default_currency')

    @property
    def events(self):
        """Shortcut for events of the patron transaction."""
        results = PatronTransactionEventsSearch()\
            .filter('term', parent__pid=self.pid).source('pid').scan()
        for result in results:
            yield PatronTransactionEvent.get_record_by_pid(result.pid)

    def get_number_of_patron_transaction_events(self):
        """Get number of patron transaction events."""
        return PatronTransactionEventsSearch()\
            .filter('term', parent__pid=self.pid).source().count()

    def get_links_to_me(self, get_pids=False):
        """Record links.

        :param get_pids: if True list of linked pids
                         if False count of linked records
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
        cannot_delete = {}
        links = self.get_links_to_me()
        if links:
            cannot_delete['links'] = links
        return cannot_delete


class PatronTransactionsIndexer(IlsRecordsIndexer):
    """Holdings indexing class."""

    record_cls = PatronTransaction

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(record_id_iterator, doc_type='pttr')
