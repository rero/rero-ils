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

"""API for manipulating Notifications."""

from __future__ import absolute_import, print_function

from copy import deepcopy
from datetime import datetime, timedelta
from functools import partial

import ciso8601
from flask import current_app
from invenio_search.api import RecordsSearch

from .dispatcher import Dispatcher
from .models import NotificationIdentifier, NotificationMetadata
from ..api import IlsRecord
from ..documents.api import Document
from ..fetchers import id_fetcher
from ..libraries.api import Library
from ..locations.api import Location
from ..minters import id_minter
from ..patrons.api import Patron
from ..providers import Provider

# notif provider
NotificationProvider = type(
    'NotificationProvider',
    (Provider,),
    dict(identifier=NotificationIdentifier, pid_type='notif')
)
# notif minter
notification_id_minter = partial(id_minter, provider=NotificationProvider)
# notif fetcher
notification_id_fetcher = partial(id_fetcher, provider=NotificationProvider)


class NotificationsSearch(RecordsSearch):
    """RecordsSearch for Notifications."""

    class Meta:
        """Search only on Notifications index."""

        index = 'notifications'


class Notification(IlsRecord):
    """Notifications class."""

    minter = notification_id_minter
    fetcher = notification_id_fetcher
    provider = NotificationProvider
    model_cls = NotificationMetadata

    def dispatch(self, delay=True):
        """Dispatch notification."""
        self = Dispatcher().dispatch_notification(notification=self)
        return self

    def update_process_date(self):
        """Update process date."""
        self['process_date'] = datetime.now().isoformat()
        self.update(data=self.dumps(), dbcommit=True, reindex=True)
        return self

    def replace_pids_and_refs(self):
        """Dumps data."""
        from ..items.api import Item
        try:
            self.init_loan()
            data = deepcopy(self.replace_refs())
            data['loan'] = self.loan
            data['loan']['item'] = self.item.replace_refs().dumps()
            # del(data['loan']['item_pid'])
            data['loan']['patron'] = self.patron.replace_refs().dumps()
            # language = data['loan']['patron']['communication_language']
            # del(data['loan']['patron_pid'])
            data['loan']['transaction_user'] = \
                self.transaction_user.replace_refs().dumps()
            # del(data['loan']['transaction_user_pid'])
            data['loan']['transaction_location'] = \
                self.transaction_location.replace_refs().dumps()
            # del(data['loan']['transaction_location_pid'])
            pickup_location = self.pickup_location
            if pickup_location:
                data['loan']['pickup_location'] = \
                    pickup_location.replace_refs().dumps()
                # del(data['loan']['pickup_location_pid'])
                library_pid = data['loan']['pickup_location']['library']['pid']
                library = Library.get_record_by_pid(library_pid)
                data['loan']['pickup_location']['library'] = library
                data['loan']['library'] = library
                keep_until = datetime.now() + timedelta(days=10)
                next_open = library.next_open(keep_until)
                # language = data['loan']['patron']['communication_language']
                next_open = next_open.strftime("%d.%m.%Y")
                data['loan']['next_open'] = next_open
            else:
                data['loan']['pickup_location'] = \
                    self.transaction_location.replace_refs().dumps()
                item_pid = data['loan']['item_pid']
                library = Item.get_record_by_pid(item_pid).get_library()
                data['loan']['library'] = library

            document = self.document.replace_refs().dumps()
            data['loan']['document'] = document
            authors = document.get('authors', '')
            if authors:
                author = authors[0].get('name', '')
                if not author:
                    mef_list = ['name_fr', 'name_de', 'name_it', 'name_en']
                    for a_name in mef_list:
                        if authors[0].get(a_name, ''):
                            author = authors[0].get(a_name)
                            break
                data['loan']['author'] = author
            end_date = data.get('loan').get('end_date')
            if end_date:
                end_date = ciso8601.parse_datetime_as_naive(end_date)
                data['loan']['end_date'] = end_date.strftime("%d.%m.%Y")
            # del(data['loan']['document_pid'])

            # create a link to patron profile
            patron = Patron.get_record_by_pid(data['loan']['patron']['pid'])
            view_code = patron.get_organisation().get('code')
            base_url = current_app.config.get('RERO_ILS_APP_BASE_URL')
            url_api = '{base_url}/{view_code}/patrons/profile'
            profile_url = url_api.format(
                base_url=base_url, view_code=view_code)
            data['loan']['profile_url'] = profile_url

            return data
        except Exception as e:
            raise(e)

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
        return self.loan.get('item_pid')

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


def get_availability_notification(loan):
    """Returns availability notification from loan."""
    results = NotificationsSearch().filter(
        'term', loan__pid=loan.pid
        ).filter('term', notification_type='availability').source().scan()
    try:
        pid = next(results).pid
        return Notification.get_record_by_pid(pid)
    except StopIteration:
        return None


def get_recall_notification(loan):
    """Returns availability notification from loan."""
    results = NotificationsSearch().filter(
        'term', loan__pid=loan.pid
        ).filter('term', notification_type='recall').source().scan()
    try:
        pid = next(results).pid
        return Notification.get_record_by_pid(pid)
    except StopIteration:
        return None


def number_of_reminders_sent(loan):
    """Get the number of overdue notifications sent for the given loan."""
    results = NotificationsSearch().filter(
        'term', loan__pid=loan.pid
        ).filter('term', notification_type='overdue').source().scan()
    try:
        pid = next(results).pid
        notification = Notification.get_record_by_pid(pid)
        return notification.get('reminder_counter')
    except StopIteration:
        return 0
