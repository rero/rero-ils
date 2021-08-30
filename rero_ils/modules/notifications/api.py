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

"""API for manipulating Notifications."""

from __future__ import absolute_import, print_function

from copy import deepcopy
from datetime import datetime
from functools import partial

import ciso8601
from flask import current_app

from .models import NotificationIdentifier, NotificationMetadata
from ..api import IlsRecord, IlsRecordsIndexer, IlsRecordsSearch
from ..documents.api import Document
from ..fetchers import id_fetcher
from ..locations.api import Location
from ..minters import id_minter
from ..patron_transactions.api import PatronTransaction, \
    PatronTransactionsSearch
from ..patrons.api import Patron
from ..providers import Provider

# notification provider
NotificationProvider = type(
    'NotificationProvider',
    (Provider,),
    dict(identifier=NotificationIdentifier, pid_type='notif')
)

# notification minter
notification_id_minter = partial(id_minter, provider=NotificationProvider)
# notification fetcher
notification_id_fetcher = partial(id_fetcher, provider=NotificationProvider)


class NotificationsSearch(IlsRecordsSearch):
    """RecordsSearch for Notifications."""

    class Meta:
        """Search only on Notifications index."""

        index = 'notifications'
        doc_types = None
        fields = ('*', )
        facets = {}

        default_filter = None


class Notification(IlsRecord):
    """Notifications class."""

    minter = notification_id_minter
    fetcher = notification_id_fetcher
    provider = NotificationProvider
    model_cls = NotificationMetadata

    @classmethod
    def create(cls, data, id_=None, delete_pid=False,
               dbcommit=False, reindex=False, **kwargs):
        """Create notification record."""
        data.setdefault('status', 'created')
        record = super().create(
            data, id_, delete_pid, dbcommit, reindex, **kwargs)
        PatronTransaction.create_patron_transaction_from_notification(
            notification=record, dbcommit=dbcommit, reindex=reindex,
            delete_pid=delete_pid)
        return record

    def update_process_date(self, sent=False, status='done'):
        """Update process date."""
        self['process_date'] = datetime.utcnow().isoformat()
        self['notification_sent'] = sent
        self['status'] = status
        return self.update(
            data=self.dumps(), commit=True, dbcommit=True, reindex=True)

    def replace_pids_and_refs(self):
        """Dumps data."""
        from .utils import get_library_metadata
        from ..items.api import Item
        self.init_loan()
        data = deepcopy(self.replace_refs())

        data['loan'] = self.loan
        data['loan']['item'] = self.item.replace_refs().dumps()
        data['loan']['patron'] = self.patron.replace_refs().dumps()
        data['loan']['transaction_user'] = \
            self.transaction_user.replace_refs().dumps()
        data['loan']['transaction_location'] = \
            self.transaction_location.replace_refs().dumps()
        pickup_location = self.pickup_location
        item_pid = data['loan']['item']['pid']
        item = Item.get_record_by_pid(item_pid)
        data['loan']['library'] = get_library_metadata(item.library_pid)

        if self.transaction_location:
            data['loan']['transaction_library'] = \
                get_library_metadata(self.transaction_location.library_pid)

        if pickup_location:
            data['loan']['pickup_location'] = \
                pickup_location.replace_refs().dumps()
            pickup_lib_pid = data['loan']['pickup_location']['library']['pid']
            library_metadata = get_library_metadata(pickup_lib_pid)
            data['loan']['pickup_library'] = library_metadata
            data['loan']['pickup_name'] = pickup_location.get(
                'pickup_name',
                data['loan']['pickup_library']['name']
            )
        elif self.transaction_location:
            data['loan']['pickup_name'] = \
                data['loan']['transaction_library']['name']

        document = self.document.replace_refs().dumps()
        data['loan']['document'] = document
        titles = document.get('title', [])
        bf_titles = list(filter(lambda t: t['type'] == 'bf:Title', titles))
        for title in bf_titles:
            data['loan']['document']['title_text'] = title['_text']

        from ..documents.views import create_title_responsibilites
        responsibility_statement = create_title_responsibilites(
            document.get('responsibilityStatement', [])
        )
        data['loan']['document']['responsibility_statement'] = \
            next(iter(responsibility_statement or []), '')

        end_date = data.get('loan').get('end_date')
        if end_date:
            end_date = ciso8601.parse_datetime(end_date)
            data['loan']['end_date'] = end_date.strftime("%d.%m.%Y")

        # create a link to patron profile
        patron = Patron.get_record_by_pid(data['loan']['patron']['pid'])
        view_code = patron.get_organisation().get('code')
        base_url = current_app.config.get('RERO_ILS_APP_URL')
        profile_url = f'{base_url}/{view_code}/patrons/profile'
        data['loan']['profile_url'] = profile_url

        return data

    def init_loan(self):
        """Set loan of the notification."""
        if not hasattr(self, 'loan'):
            from ..loans.api import Loan
            self.loan = Loan.get_record_by_pid(self.loan_pid)
        return self.loan

    @property
    def loan_pid(self):
        """Shortcut for loan pid of the notification."""
        return self.replace_refs()['loan']['pid']

    @property
    def organisation_pid(self):
        """Get organisation pid for notification."""
        self.init_loan()
        return self.transaction_location.organisation_pid

    @property
    def item_pid(self):
        """Shortcut for item pid of the notification."""
        self.init_loan()
        return self.loan.get('item_pid', {}).get('value')

    @property
    def item(self):
        """Shortcut for item of the notification."""
        from ..items.api import Item
        return Item.get_record_by_pid(self.item_pid)

    @property
    def patron_pid(self):
        """Shortcut for patron pid of the notification."""
        self.init_loan()
        return self.loan.get('patron_pid')

    @property
    def patron(self):
        """Shortcut for patron of the notification."""
        return Patron.get_record_by_pid(self.patron_pid)

    @property
    def transaction_user_pid(self):
        """Shortcut for transaction user pid of the notification."""
        self.init_loan()
        return self.loan.get('transaction_user_pid')

    @property
    def transaction_user(self):
        """Shortcut for transaction user of the notification."""
        return Patron.get_record_by_pid(self.transaction_user_pid)

    @property
    def transaction_library_pid(self):
        """Shortcut for transaction library pid of the notification."""
        location = self.transaction_location
        return location.library_pid

    @property
    def transaction_location_pid(self):
        """Shortcut for transaction location pid of the notification."""
        self.init_loan()
        return self.loan.get('transaction_location_pid')

    @property
    def transaction_location(self):
        """Shortcut for transaction location of the notification."""
        return Location.get_record_by_pid(self.transaction_location_pid)

    @property
    def pickup_location_pid(self):
        """Shortcut for pickup location pid of the notification."""
        self.init_loan()
        return self.loan.get('pickup_location_pid')

    @property
    def pickup_location(self):
        """Shortcut for pickup location of the notification."""
        return Location.get_record_by_pid(self.pickup_location_pid)

    @property
    def document_pid(self):
        """Shortcut for document pid of the notification."""
        self.init_loan()
        return self.loan.get('document_pid')

    @property
    def document(self):
        """Shortcut for document of the notification."""
        return Document.get_record_by_pid(self.document_pid)

    @property
    def patron_transactions(self):
        """Returns patron transactions attached of a notification."""
        results = PatronTransactionsSearch()\
            .filter('term', notification__pid=self.pid)\
            .source(['pid']).scan()
        for result in results:
            yield PatronTransaction.get_record_by_pid(result.pid)


class NotificationsIndexer(IlsRecordsIndexer):
    """Holdings indexing class."""

    record_cls = Notification

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(record_id_iterator, doc_type='notif')
