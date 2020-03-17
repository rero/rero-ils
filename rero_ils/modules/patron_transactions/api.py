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
from ..utils import get_ref_for_pid

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
               dbcommit=False, reindex=False, **kwargs):
        """Create patron transaction record."""
        record = super(PatronTransaction, cls).create(
            data, id_, delete_pid, dbcommit, reindex, **kwargs)
        PatronTransactionEvent.create_event_from_patron_transaction(
            patron_transaction=record, dbcommit=dbcommit, reindex=reindex,
            delete_pid=delete_pid, update_parent=False)
        return record

    @classmethod
    def _build_transaction_query(cls, patron_pid, status=None):
        """Private function to build a transaction query linked to a patron."""
        query = PatronTransactionsSearch() \
            .filter('term', patron__pid=patron_pid)
        if status:
            query = query.filter('term', status=status)
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
    def get_transactions_count_for_patron(cls, patron_pid, status=None):
        """Get patron transactions count linked to a patron.

        :param patron_pid: the patron pid being searched
        :param status: (optional) transaction status filter,
        """
        query = cls._build_transaction_query(patron_pid, status)
        return query.source().count()

    @property
    def loan_pid(self):
        """Return the loan pid of the the overdue patron transaction."""
        from ..notifications.api import Notification
        if self.notification_pid:
            notif = Notification.get_record_by_pid(self.notification_pid)
            return notif.loan_pid

    @property
    def document_pid(self):
        """Return the document pid of the the overdue patron transaction."""
        from ..notifications.api import Notification
        if self.notification_pid:
            notif = Notification.get_record_by_pid(self.notification_pid)
            return notif.document_pid

    @property
    def patron_pid(self):
        """Return the patron pid of the patron transaction."""
        return self.replace_refs()['patron']['pid']

    @property
    def total_amount(self):
        """Return the total_amount of the patron transaction."""
        return self.get('total_amount')

    @property
    def notification_pid(self):
        """Return the notification pid of the patron transaction."""
        if self.get('notification'):
            return self.replace_refs()['notification']['pid']

    @property
    def notification(self):
        """Return the notification of the patron transaction."""
        from ..notifications.api import Notification
        if self.get('notification'):
            pid = self.replace_refs()['notification']['pid']
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
    def create_patron_transaction_from_notification(
            cls, notification=None, dbcommit=None, reindex=None,
            delete_pid=None):
        """Create a patron transaction from notification."""
        from ..notifications.api import calculate_overdue_amount
        record = {}
        if notification.get('notification_type') == 'overdue':
            data = {
                'notification': {
                    '$ref': get_ref_for_pid('notif', notification.pid)
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
                'total_amount': calculate_overdue_amount(notification),
                'creation_date': datetime.now(timezone.utc).isoformat(),
                'type': 'overdue',
                'status': 'open'
            }
            record = cls.create(
                data,
                dbcommit=dbcommit,
                reindex=reindex,
                delete_pid=delete_pid
            )
        return record

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
            .filter('term', parent__pid=self.pid)\
            .source()\
            .scan()
        for result in results:
            yield PatronTransactionEvent.get_record_by_pid(result.pid)

    def get_number_of_patron_transaction_events(self):
        """Get number of patron transaction events."""
        return PatronTransactionEventsSearch()\
            .filter('term', parent__pid=self.pid)\
            .source()\
            .count()

    def get_links_to_me(self):
        """Get number of links."""
        links = {}
        events = self.get_number_of_patron_transaction_events()
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
