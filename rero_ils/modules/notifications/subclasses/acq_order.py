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

"""API for manipulating "order" acquisition notifications."""

from __future__ import absolute_import, print_function

from flask import current_app
from werkzeug.utils import cached_property

from rero_ils.modules.acquisition.acq_orders.dumpers import \
    AcqOrderNotificationDumper
from rero_ils.modules.libraries.api import Library
from rero_ils.modules.notifications.api import Notification
from rero_ils.modules.notifications.models import NotificationChannel, \
    NotificationType, RecipientType
from rero_ils.modules.utils import extracted_data_from_ref


class AcquisitionOrderNotification(Notification):
    """Acquisition order notifications class.

    An acquisition order notification is a message send to the vendor to order
    an acquisition order that contains some acquisition order lines. it should
    never be cancelled and is always sent by email (for now).

    Acquisition order notification works synchronously. This means it will be
    send just after the creation. This also means that it should never be
    aggregated.
    """

    def extended_validation(self, **kwargs):
        """Validate record against schema.

        and extended validation to check that notification is indeed of type
        acquisition order and it has a valid order pid in its context.
        """
        if self.type != NotificationType.ACQUISITION_ORDER:
            return f"'{self.type} isn't an AcquisitionNotification"
        if not self.acq_order_pid:
            return '`order` field must be specified into `context` for ' \
                   'AcquisitionNotification'

        # validate that at least one email of type `to` exist and one email of
        # type `reply_to` is given in the ist of emails.
        recipient_types = {
            recipient.get('type')
            for recipient in self.get('context', {}).get('recipients', [])
        }
        if RecipientType.TO not in recipient_types \
           or RecipientType.REPLY_TO not in recipient_types:
            return 'Recipient type `to` and `reply_to` are required'
        return True

    # PARENT ABSTRACT IMPLEMENTATION METHODS ==================================
    #  Implementation of `Notification` parent class abstract methods.
    @property
    def organisation_pid(self):
        """Get organisation pid for this notification.

        The acquisition order notification inherits its organisation links from
        its parent (order) record.
        """
        return self.order.organisation_pid

    @property
    def aggregation_key(self):
        """Get the aggregation key for this notification.

        No aggregation needed for the acquisition order notification, as such,
        we return the string type of the notification id.
        """
        return str(self.id)

    def can_be_cancelled(self):
        """Check if a notification can be cancelled.

        As notification process can be asynchronous, in some case, when the
        notification is processed, it's not anymore required to be sent.
        The acquisition order notification ca not be cancelled.

        :return a tuple with two values: a boolean to know if the notification
                can be cancelled; the reason why the notification can be
                cancelled (only present if tuple first value is True).
        """
        if not self.order:
            return True, "Order doesn't exists anymore"
        return False, None

    def get_communication_channel(self):
        """Get the communication channel to use for this notification."""
        # For now, the channel for sending the acquisition order notification
        # is always email.
        return NotificationChannel.EMAIL

    def get_language_to_use(self):
        """Get the language to use for dispatching the notification."""
        # By default, the language to use to build the notification is defined
        # in the vendor setting. Override this method if needed in the future.
        return self.order.vendor.get(
            'communication_language',
            current_app.config.get('RERO_ILS_APP_DEFAULT_LANGUAGE', 'eng')
        )

    def get_template_path(self):
        """Get the template to use to render the notification."""
        # By default, the template path to use reflects the notification type.
        # Override this method if necessary
        return \
            f'rero_ils/vendor_order_mail/{self.get_language_to_use()}.tpl.txt'

    def get_recipients(self, address_type):
        """Get the notification recipients email address.

        If the notification should be dispatched by email (see
        ``Notification.get_communication_channel()``, this method must return
        the list of email addresses where to send the notification to.

        :param address_type: the recipient address type.
        :returns: email addresses list where send the notification to.
        """
        return [
            recipient.get('address')
            for recipient in self.get('context', {}).get('recipients', [])
            if recipient.get('type') == address_type
        ]

    @classmethod
    def get_notification_context(cls, notifications=None):
        """Get the context to use to render the corresponding template.

        :param notifications: an array of ``Notification`` to parse to extract
            the required data to build the template.
        :returns: a ``dict`` containing all required data to build the
            template.
        """
        notifications = notifications or []
        if not notifications:
            return {}

        notification = notifications[0]
        order = notification.order
        return {'order': order.dumps(dumper=AcqOrderNotificationDumper())}

    # GETTER & SETTER METHODS =================================================
    #  Shortcuts to easy access notification attributes.

    @property
    def acq_order_pid(self):
        """Shortcut for acq order pid of the notification."""
        return extracted_data_from_ref(self['context']['order'])

    @cached_property
    def order(self):
        """Shortcut for acquisition order related to the notification."""
        return extracted_data_from_ref(self['context']['order'], data='record')

    @property
    def library_pid(self):
        """Get the library pid related to the notification."""
        return self.order.library_pid

    @cached_property
    def library(self):
        """Shortcut for library of the notification."""
        return Library.get_record_by_pid(self.library_pid)
