# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
# Copyright (C) 2019-2023 UCLouvain
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

"""API for manipulating "claim" notifications about serial issue."""

from __future__ import absolute_import, print_function

from abc import ABC, abstractmethod

from werkzeug.utils import cached_property

from rero_ils.modules.items.dumpers import ClaimIssueNotificationDumper
from rero_ils.modules.notifications.api import Notification
from rero_ils.modules.notifications.models import NotificationChannel, \
    NotificationType, RecipientType
from rero_ils.modules.utils import extracted_data_from_ref


class ClaimSerialIssueNotification(Notification, ABC):
    """Claim serial issue notifications class.

    A claim notification is a message sent to the vendor of the serial to
    specify if an issue isn't received as expected. It should never be
    cancelled (except if issue item doesn't exist anymore) and is always sent
    by email (for now).

    Claim issue notification works synchronously. This means it will be sent
    just after the creation. This also means that it should never be
    aggregated.
    """

    def extended_validation(self, **kwargs):
        """Validate record against schema.

        :params kwargs: additional named arguments.
        :returns: True if all checks are ok; a string representing the problem
            if a problem is detected.
        :rtype: boolean|str
        """
        if self.type != NotificationType.CLAIM_ISSUE:
            return f"'{self.type} isn't an ClaimSerialIssueNotification"
        if not self.item:
            return '`item` field must be specified into `context` for ' \
                   'ClaimSerialIssueNotification'
        if not self.item.is_issue:
            return '`item` field must reference an serial issue item.'

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
        """Get organisation pid for this notification."""
        return self.item.organisation_pid

    @property
    def aggregation_key(self):
        """Get the aggregation key for this notification.

        No aggregation needed for the claim issue notification, as such,
        we return the string type of the notification id.
        """
        return str(self.id)

    def can_be_cancelled(self):
        """Check if a notification can be cancelled.

        As notification process can be asynchronous, in some case, when the
        notification is processed, it's not anymore required to be sent.
        The acquisition order notification ca not be cancelled.

        :returns: a tuple with two values: a boolean to know if the
            notification can be cancelled; the reason why the notification can
            be cancelled (only present if tuple first value is True).
        """
        if not self.item:
            return True, "Item doesn't exists anymore"
        return False, None

    def get_communication_channel(self):
        """Get the communication channel to use for this notification."""
        # For now, the channel for sending the claim issue notification is
        # always email.
        return NotificationChannel.EMAIL

    def get_language_to_use(self):
        """Get the language to use for dispatching the notification."""
        # By default, the language to use to build the notification is defined
        # in the vendor setting. Override this method if needed in the future.
        return self.vendor.get('communication_language')

    def get_template_path(self):
        """Get the template to use to render the notification."""
        # By default, the template path to use reflects the notification type.
        # Override this method if necessary
        return f'email/{self.type}/{self.get_language_to_use()}.tpl.txt'

    def get_recipients(self, address_type):
        """Get the notification recipients email address.

        If the notification should be dispatched by email (see
        ``Notification.get_communication_channel()``, this method must return
        the list of email addresses where to send the notification to.

        :param address_type: the recipient address type.
        :returns: email addresses list where send the notification to.
        :rtype: list<{type: str, address: str}>
        """
        return [
            recipient.get('address')
            for recipient in self.get('context', {}).get('recipients', [])
            if recipient.get('type') == address_type
        ]

    @classmethod
    @abstractmethod
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
        item = notification.item
        return {'issue': item.dumps(dumper=ClaimIssueNotificationDumper())}

    # GETTER & SETTER METHODS =================================================
    #  Shortcuts to easy access notification attributes.
    @property
    def item_pid(self):
        """Shortcut for item pid related to the notification."""
        return extracted_data_from_ref(self['context']['item'])

    @property
    def item(self):
        """Shortcut for item related to the notification."""
        return extracted_data_from_ref(self['context']['item'], data='record')

    @cached_property
    def vendor(self):
        """Shortcut for vendor of the issue."""
        if self.item and (holding := self.item.holding):
            return holding.vendor

    @property
    def library(self):
        """Shortcut for library related to the issue."""
        if self.item and (holding := self.item.holding):
            return holding.library
