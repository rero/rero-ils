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

from abc import ABC, abstractmethod
from datetime import datetime
from functools import partial

from flask import current_app

from .extensions import NotificationSubclassExtension
from .models import NotificationIdentifier, NotificationMetadata, \
    NotificationStatus
from ..api import IlsRecord, IlsRecordsIndexer, IlsRecordsSearch
from ..fetchers import id_fetcher
from ..minters import id_minter
from ..patron_transactions.api import PatronTransaction, \
    PatronTransactionsSearch
from ..patron_transactions.utils import \
    create_patron_transaction_from_notification
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


class Notification(IlsRecord, ABC):
    """Notifications class.

    A Notification is an abstract class representing a message to be sent to a
    recipient. All the notification workflow depends of the notification type.
    The recipient, the dispatcher method, notification aggregation... all
    these settings or behaviors must be specified into a concrete
    ``Notification`` subclass.

    But all notifications (whatever the notification type) are stored in the
    same resource and share the same JSON schema. So, this parent class defines
    every Invenio resource configuration : minters, fetchers, API methods...

    When a ``Notification`` is created or loaded, this is the
    ``NotificationSubclassExtension`` extension which determine the best
    possible concrete subclass (see this extension for more information).

      # >>> notif = Notification.get_record_by_pid('n1')
      # >>> print(type(notif))
      # >>>   <class 'ConcreteNotificationSubclass'>

    """

    minter = notification_id_minter
    fetcher = notification_id_fetcher
    provider = NotificationProvider
    model_cls = NotificationMetadata

    _extensions = [
        NotificationSubclassExtension()
    ]

    # INVENIO API METHODS =====================================================
    #   Override some invenio ``RecordBase`` method
    @classmethod
    def create(cls, data, id_=None, delete_pid=False, dbcommit=False,
               reindex=False, **kwargs):
        """Create notification record."""
        # Check if the notification_type is disabled by app configuration
        if data.get('notification_type') in current_app.config.get(
                'RERO_ILS_DISABLED_NOTIFICATION_TYPE', []):
            return

        data.setdefault('status', NotificationStatus.CREATED)
        record = super().create(data, id_, delete_pid, dbcommit, reindex,
                                **kwargs)
        create_patron_transaction_from_notification(
            notification=record, dbcommit=dbcommit, reindex=reindex,
            delete_pid=delete_pid
        )
        return record

    # ABSTRACT METHODS ========================================================
    #   All concrete subclasses MUST implement all abstract methods defined
    #   below.
    #   Note about `@property` methods : if the method isn't relevant
    #   for the subclass notification, return a default value anyway. All of
    #   these properties are use to dispatch/aggregate the notification.

    @property
    @abstractmethod
    def organisation_pid(self):
        """Get organisation pid for notification."""
        raise NotImplementedError()

    @property
    @abstractmethod
    def aggregation_key(self):
        """Get the key used to aggregate multiple notifications.

        Depending of the notification type, notifications could be aggregated
        into a single message (4 recall notification for the same patron should
        be send into the same message).

        :return the key to use to aggregate several notifications.
        """
        raise NotImplementedError()

    @abstractmethod
    def can_be_cancelled(self):
        """Determine if the notification can be cancelled.

        In case of asynchronous notification, sometimes it's not necessary
        anymore to process the notification because related resources are
        changed since the notification creation timestamp.

        :return a tuple with two values: a boolean to know if the notification
                can be cancelled; the reason why the notification can be
                cancelled (only present if tuple first value is True).
        """
        raise NotImplementedError()

    @abstractmethod
    def get_template_path(self):
        """Get the template file to use to render the notification.

        :return: the path to the Jinja template file.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_communication_channel(self):
        """Get the communication channel to use for this notification.

        The communication channel to use depends of each notification type. It
        could depends of the recipient, the template to use, ...

        :return the `NotificationChannel` to use to send the notification.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_language_to_use(self):
        """Get the language to use for dispatching the notification.

        :return return the language iso code (alpha3) to use.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_recipients(self, address_type):
        """Get the notification recipients email address.

        If the notification should be dispatched by email (see
        ``Notification.get_communication_channel()``, this method must return
        the list of email addresses where to send the notification to.

        :param address_type: the type of address to get (to, cc, reply_to, ...)
        :return return email addresses list where send the notification to.
        """
        raise NotImplementedError()

    @classmethod
    @abstractmethod
    def get_notification_context(cls, notifications=None):
        """Get the context to use to render the corresponding template.

        :param notifications: an array of ``Notification`` to parse to extract
                              the required data to build the template.
        :return: a ``dict`` containing all required data to build the template.
        """
        raise NotImplementedError()

    # GETTER METHODS ==========================================================

    @property
    def type(self):
        """Shortcut for notification type."""
        return self.get('notification_type')

    @property
    def status(self):
        """Shortcut for notification status."""
        return self.get('status')

    @property
    def patron_transactions(self):
        """Returns patron transactions attached of a notification."""
        results = PatronTransactionsSearch()\
            .filter('term', notification__pid=self.pid)\
            .source(False).scan()
        for result in results:
            yield PatronTransaction.get_record_by_id(result.meta.id)

    # CLASS METHODS ===========================================================
    def update_process_date(self, sent=False, status=NotificationStatus.DONE):
        """Update the notification to set process date.

        :param sent: is the notification is sent.
        :param status: the new notification status.
        :return the updated notification.
        """
        self['process_date'] = datetime.utcnow().isoformat()
        self['notification_sent'] = sent
        self['status'] = status
        return self.update(
            data=self.dumps(), commit=True, dbcommit=True, reindex=True)


class NotificationsIndexer(IlsRecordsIndexer):
    """Holdings indexing class."""

    record_cls = Notification

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(record_id_iterator, doc_type='notif')
