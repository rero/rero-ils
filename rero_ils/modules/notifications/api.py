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

from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from functools import partial

import ciso8601
from celery import current_app as current_celery_app
from flask import current_app
from kombu import Exchange, Producer, Queue
from kombu.compat import Consumer
from sqlalchemy.orm.exc import NoResultFound

from .dispatcher import Dispatcher
from .models import NotificationIdentifier, NotificationMetadata
from ..api import IlsRecord, IlsRecordsIndexer, IlsRecordsSearch
from ..circ_policies.api import DUE_SOON_REMINDER_TYPE, \
    OVERDUE_REMINDER_TYPE, CircPolicy
from ..documents.api import Document
from ..fetchers import id_fetcher
from ..libraries.api import Library
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

    RECALL_NOTIFICATION_TYPE = 'recall'
    AVAILABILITY_NOTIFICATION_TYPE = 'availability'
    DUE_SOON_NOTIFICATION_TYPE = 'due_soon'
    OVERDUE_NOTIFICATION_TYPE = 'overdue'

    minter = notification_id_minter
    fetcher = notification_id_fetcher
    provider = NotificationProvider
    model_cls = NotificationMetadata
    mq_routing_key = 'notification'
    mq_exchange = Exchange(mq_routing_key, type='direct')
    mq_queue = Queue(
        mq_routing_key,
        exchange=Exchange(mq_routing_key, type='direct'),
        routing_key=mq_routing_key
    )

    @classmethod
    def create(cls, data, id_=None, delete_pid=False,
               dbcommit=False, reindex=False, **kwargs):
        """Create notification record."""
        record = super().create(
            data, id_, delete_pid, dbcommit, reindex, **kwargs)
        PatronTransaction.create_patron_transaction_from_notification(
            notification=record, dbcommit=dbcommit, reindex=reindex,
            delete_pid=delete_pid)
        return record

    def update_process_date(self):
        """Update process date."""
        self['process_date'] = datetime.now(timezone.utc).isoformat()
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
                keep_until = datetime.now(timezone.utc) + timedelta(days=10)
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
            # del(data['loan']['document_pid'])

            # create a link to patron profile
            patron = Patron.get_record_by_pid(data['loan']['patron']['pid'])
            view_code = patron.get_organisation().get('code')
            profile_url = '{base_url}/{view_code}/patrons/profile'.format(
                base_url=current_app.config.get('RERO_ILS_APP_URL'),
                view_code=view_code
            )
            data['loan']['profile_url'] = profile_url

            return data
        except Exception as error:
            raise(error)

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

    def dispatch(self, enqueue=True, verbose=False):
        """Dispatch notification."""
        if enqueue:
            with self.create_producer() as producer:
                producer.publish(dict(pid=self.pid))
        else:
            self = Dispatcher().dispatch_notification(notification=self,
                                                      verbose=verbose)
        return self

    @contextmanager
    def create_producer(self):
        """Context manager that yields an instance of ``Producer``."""
        with current_celery_app.pool.acquire(block=True) as conn:
            yield Producer(
                conn,
                exchange=self.mq_exchange,
                routing_key=self.mq_routing_key,
                auto_declare=True,
            )

    @classmethod
    def process_notifications(cls, verbose=False):
        """Process notifications queue."""
        count = {'send': 0, 'reject': 0, 'error': 0}
        with current_celery_app.pool.acquire(block=True) as conn:
            consumer = Consumer(
                connection=conn,
                queue=cls.mq_queue.name,
                exchange=cls.mq_exchange.name,
                routing_key=cls.mq_routing_key,
            )

            for message in consumer.iterqueue():
                payload = message.decode()
                try:
                    pid = payload['pid']
                    notification = Notification.get_record_by_pid(pid)
                    Dispatcher().dispatch_notification(notification, verbose)
                    message.ack()
                    count['send'] += 1
                except NoResultFound:
                    message.reject()
                    count['reject'] += 1
                except Exception:
                    message.reject()
                    current_app.logger.error(
                        "Failed to dispatch notification {pid}".format(
                            pid=payload.get('pid')
                        ),
                        exc_info=True
                    )
                    count['error'] += 1
            consumer.close()

        return count


class NotificationsIndexer(IlsRecordsIndexer):
    """Holdings indexing class."""

    record_cls = Notification

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(record_id_iterator, doc_type='notif')


def get_notification(loan, notification_type):
    """Returns specific notification from loan.

    :param loan: the parent loan.
    :param notification_type: the type of notification sent.
    """
    results = NotificationsSearch()\
        .filter('term', loan__pid=loan.pid)\
        .filter('term', notification_type=notification_type)\
        .source().scan()
    try:
        pid = next(results).pid
        return Notification.get_record_by_pid(pid)
    except StopIteration:
        return None


def number_of_reminders_sent(
        loan, notification_type=Notification.OVERDUE_NOTIFICATION_TYPE):
    """Get the number of notifications sent for the given loan.

    :param loan: the parent loan.
    :param notification_type: the type of notification to find.
    """
    return NotificationsSearch()\
        .filter('term', loan__pid=loan.pid)\
        .filter('term', notification_type=notification_type) \
        .source().count()


def get_communication_channel_to_use(loan, notification_data, patron):
    """Get the communication channel to use for a notification.

    :param loan: the notification parent loan.
    :param notification_data: the notification data.
    :param patron: the patron related to this notification
    :return the communication channel to use for this notification
    """
    from ..loans.utils import get_circ_policy
    communication_channel = 'patron_setting'

    # 'overdue' and 'due_soon' notification type could define a communication
    # channel that can override the patron setting.
    notification_type = notification_data.get('notification_type')
    if notification_type in [Notification.OVERDUE_NOTIFICATION_TYPE,
                             Notification.DUE_SOON_NOTIFICATION_TYPE]:
        cipo = get_circ_policy(loan)
        reminder_type = DUE_SOON_REMINDER_TYPE
        if notification_type != Notification.DUE_SOON_NOTIFICATION_TYPE:
            reminder_type = OVERDUE_REMINDER_TYPE
        reminder = cipo.get_reminder(
            reminder_type=reminder_type,
            idx=notification_data.get('reminder_counter', 0)
        )
        communication_channel = reminder.get('communication_channel')

    # return the best communication channel
    if communication_channel == 'patron_setting':
        return patron['patron']['communication_channel']
    else:
        return communication_channel


def get_template_to_use(loan, notification_data):
    """Get the template path to use for a notification.

    :param loan: the notification parent loan.
    :param notification_data: the notification data.
    """
    from ..loans.utils import get_circ_policy

    # depending of notification to send, the template to use could be static or
    # found into the related circulation policy.
    # TODO : depending of the communication channel, improve the function to
    #        get the correct template.
    notification_type = notification_data.get('notification_type')
    static_template_mapping = {
        Notification.RECALL_NOTIFICATION_TYPE: 'email/recall',
        Notification.AVAILABILITY_NOTIFICATION_TYPE: 'email/availability'
    }
    if notification_type in static_template_mapping:
        return static_template_mapping[notification_type]

    # Find the related circulation policy and check about the template to use
    # into the defined reminders
    cipo = get_circ_policy(loan)
    reminder_type = DUE_SOON_REMINDER_TYPE
    if notification_type != Notification.DUE_SOON_NOTIFICATION_TYPE:
        reminder_type = OVERDUE_REMINDER_TYPE
    reminder = cipo.get_reminder(
        reminder_type=reminder_type,
        idx=notification_data.get('reminder_counter', 0)
    )
    return reminder.get('template')


def calculate_notification_amount(notification):
    """Return amount due for a notification.

    :param notification: the notification for which to compute the amount. At
                         this time, this is not yet a `Notification`, only a
                         dict of structured data.
    :return the amount due for this notification. 0 if no amount could be
            compute.
    """
    # Find the reminder type to use based on the notification that we would
    # sent. If no reminder type is found, then no amount could be calculated
    # and we can't return '0'
    notif_type = notification.get('notification_type')
    reminder_type_mapping = {
        Notification.DUE_SOON_NOTIFICATION_TYPE: DUE_SOON_REMINDER_TYPE,
        Notification.OVERDUE_NOTIFICATION_TYPE: OVERDUE_REMINDER_TYPE
    }
    reminder_type = reminder_type_mapping.get(notif_type)
    if not notif_type or not reminder_type:
        return 0

    # to find the notification due amount, we firstly need to get the
    # circulation policy linked to the parent loan.
    location_pid = notification.transaction_location_pid
    location = Location.get_record_by_pid(location_pid)
    cipo = CircPolicy.provide_circ_policy(
        location.organisation_pid,
        location.library_pid,
        notification.patron.patron_type_pid,
        notification.item.holding_circulation_category_pid
    )

    # now we get the circulation policy, we need to find the right reminder
    # to use for this notification. To know that, we firstly need to know how
    # many notification are already sent for the parent loan for the same
    # notification type.
    reminders_count = number_of_reminders_sent(
        notification.loan, notification_type=notif_type)
    reminder = cipo.get_reminder(
        reminder_type=reminder_type,
        idx=reminders_count-1
    )
    return reminder.get('fee_amount', 0) if reminder else 0
