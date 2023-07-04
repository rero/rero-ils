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

"""API for manipulating circulation notifications."""

from __future__ import absolute_import, print_function

import hashlib
from abc import ABC

from werkzeug.utils import cached_property

from rero_ils.modules.documents.api import Document
from rero_ils.modules.items.api import Item
from rero_ils.modules.libraries.api import Library
from rero_ils.modules.loans.api import Loan, LoanState
from rero_ils.modules.locations.api import Location
from rero_ils.modules.patrons.api import Patron
from rero_ils.modules.utils import extracted_data_from_ref

from ..api import Notification
from ..models import NotificationChannel, NotificationType, RecipientType


class CirculationNotification(Notification, ABC):
    """Circulation notifications class."""

    def extended_validation(self, **kwargs):
        """Validate record against schema.

        and extended validation to check that patron types and item types are
        part of the correct organisation.
        """
        if self.type not in NotificationType.CIRCULATION_NOTIFICATIONS:
            return f"'{self.type} isn't a CirculationNotification"
        if not self.loan_pid:
            return '`loan` field must be specified into `context` for ' \
                   'CirculationNotification'
        return True

    # PARENT ABSTRACT IMPLEMENTATION METHODS ==================================
    #  Implementation of `Notification` parent class abstract methods.
    @property
    def organisation_pid(self):
        """Get organisation pid for this notification."""
        return self.transaction_location.organisation_pid

    @property
    def aggregation_key(self):
        """Get the aggregation key for this notification."""
        # CirculationNotification could be aggregated. 4 parts compose the
        # aggregation key (in this order):
        #   - the template to use
        #   - the communication channel of the notification
        #   - the notification sender (library)
        #   - the notification recipient (patron || library)
        parts = [
            self.get_template_path(),
            self.get_communication_channel(),
            self.library_pid,
            self.patron_pid
        ]
        return hashlib.md5(str(parts).encode()).hexdigest()

    def can_be_cancelled(self):
        """Check if a notification can be cancelled.

        As notification process can be asynchronous, in some case, when the
        notification is processed, it's not anymore required to be sent.
        By example, an AVAILABLE notification should not be sent if the
        related loan item is already in ON_LOAN state.

        :return a tuple with two values: a boolean to know if the notification
                can be cancelled; the reason why the notification can be
                cancelled (only present if tuple first value is True).
        """
        if not self.item:
            return True, "Item doesn't exists anymore"
        return False, None

    def get_communication_channel(self):
        """Get the communication channel to use for this notification."""
        # By default the circulation notification should be send depending of
        # the patron setting. Override this method if necessary
        return self.patron.get('patron', {}).get('communication_channel')

    def get_language_to_use(self):
        """Get the language to use for dispatching the notification."""
        # By default, the language to use to build the notification is defined
        # in the patron setting. Override this method if the patron isn't the
        # recipient of this notification.
        return self.patron.get('patron', {}).get('communication_language')

    def get_template_path(self):
        """Get the template to use to render the notification."""
        # By default, the template path to use reflects the notification type.
        # Override this method if necessary
        return f'email/{self.type}/{self.get_language_to_use()}.txt'

    def get_recipients(self, address_type):
        """Get the notification recipient email addresses."""
        mapping = {
            RecipientType.TO: self.get_recipients_to,
            RecipientType.REPLY_TO: self.get_recipients_reply_to
        }
        return mapping[address_type]() if address_type in mapping else []

    def get_recipients_reply_to(self):
        """Get the notification email address for 'REPLY_TO' recipient type."""
        return [self.library.get('email')]

    def get_recipients_to(self):
        """Get the notification email address for 'TO' recipient type."""
        addresses = []
        if self.get_communication_channel() == NotificationChannel.EMAIL \
           and self.patron:
            addresses = [
                self.patron.user.email,
                self.patron['patron'].get('additional_communication_email')
            ]
            addresses = [address for address in addresses if address]
        return addresses

    # GETTER & SETTER METHODS =================================================
    #  Shortcuts to easy access notification attributes.
    @property
    def loan_pid(self):
        """Shortcut for loan pid of the notification."""
        return extracted_data_from_ref(self['context']['loan'])

    @cached_property
    def loan(self):
        """Shortcut for loan related to the notification."""
        return Loan.get_record_by_pid(self.loan_pid)

    @property
    def item_pid(self):
        """Shortcut for item pid of the notification."""
        return self.loan.get('item_pid', {}).get('value')

    @cached_property
    def item(self):
        """Shortcut for item related to the notification."""
        return Item.get_record_by_pid(self.item_pid)

    @property
    def location_pid(self):
        """Get the location pid related to the notification."""
        return self.item.location_pid

    @cached_property
    def location(self):
        """Shortcut for item location of the notification."""
        return Location.get_record_by_pid(self.location_pid)

    @property
    def library_pid(self):
        """Get the library pid related to the notification."""
        return self.item.library_pid

    @cached_property
    def library(self):
        """Shortcut for item library of the notification."""
        return Library.get_record_by_pid(self.library_pid)

    @property
    def patron_pid(self):
        """Shortcut for patron pid of the notification."""
        return self.loan.get('patron_pid')

    @cached_property
    def patron(self):
        """Shortcut for patron of the notification."""
        return Patron.get_record_by_pid(self.patron_pid)

    @property
    def transaction_user_pid(self):
        """Shortcut for transaction user pid of the notification."""
        return self.loan.get('transaction_user_pid')

    @cached_property
    def transaction_user(self):
        """Shortcut for transaction user of the notification."""
        return Patron.get_record_by_pid(self.transaction_user_pid)

    @property
    def transaction_library_pid(self):
        """Shortcut for transaction library pid of the notification."""
        return self.transaction_location.library_pid

    @cached_property
    def transaction_library(self):
        """Shortcut to get notification transaction library."""
        return Library.get_record_by_pid(self.transaction_library_pid)

    @property
    def transaction_location_pid(self):
        """Shortcut for transaction location pid of the notification."""
        return self.loan.get('transaction_location_pid')

    @cached_property
    def transaction_location(self):
        """Shortcut for transaction location of the notification."""
        return Location.get_record_by_pid(self.transaction_location_pid)

    @property
    def pickup_location_pid(self):
        """Shortcut for pickup location pid of the notification."""
        return self.loan.get('pickup_location_pid')

    @cached_property
    def pickup_location(self):
        """Shortcut for pickup location of the notification."""
        return Location.get_record_by_pid(self.pickup_location_pid)

    @cached_property
    def pickup_library(self):
        """Shortcut for pickup library of the notification."""
        return self.pickup_location.get_library()

    @property
    def document_pid(self):
        """Shortcut for document pid of the notification."""
        return self.loan.get('document_pid')

    @cached_property
    def document(self):
        """Shortcut for document of the notification."""
        return Document.get_record_by_pid(self.document_pid)

    @cached_property
    def request_loan(self):
        """Get the request loan related to this notification."""
        return self.item.get_first_loan_by_state(LoanState.ITEM_AT_DESK) \
            or self.item.get_first_loan_by_state(
                LoanState.ITEM_IN_TRANSIT_FOR_PICKUP) \
            or self.item.get_first_loan_by_state(LoanState.PENDING)
