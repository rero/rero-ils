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

"""API for manipulating "booking" circulation notifications."""

from __future__ import absolute_import, print_function

import hashlib

from rero_ils.filter import format_date_filter
from rero_ils.modules.documents.dumpers import document_title_dumper
from rero_ils.modules.items.dumpers import ItemNotificationDumper
from rero_ils.modules.loans.api import LoanState
from rero_ils.modules.locations.api import Location
from rero_ils.modules.patrons.api import Patron
from rero_ils.modules.patrons.dumpers import PatronNotificationDumper
from rero_ils.utils import language_iso639_2to1

from .circulation import CirculationNotification
from ..models import NotificationChannel


class BookingCirculationNotification(CirculationNotification):
    """Booking circulation notifications class.

    A booking notification is a message send to a library to notify that a
    check in item is requested by a patron. As it's a internal notification, it
    should never be cancelled (except if the requested item doesn't exist
    anymore) and are always send by email.

    Booking notification works synchronously. This means it will be send just
    after the creation. This also means that it should never be aggregated.
    """

    @property
    def aggregation_key(self):
        """Get the aggregation key for this notification."""
        # Booking notifications must be send to a pickup library. No need to
        # take care of the notification related patron.
        lib = self.pickup_library or self.transaction_library
        parts = [
            self.get_template_path(),
            self.get_communication_channel(),
            lib.pid,
        ]
        return hashlib.md5(str(parts).encode()).hexdigest()

    def get_communication_channel(self):
        """Get the communication channel to dispatch the notification."""
        return NotificationChannel.EMAIL

    def get_language_to_use(self):
        """Get the language to use when dispatching the notification."""
        lib = self.pickup_library or self.transaction_library
        return lib.get('communication_language')

    def get_recipients_to(self):
        """Get notification email addresses for 'TO' recipient type."""
        # Booking notification will be sent to the loan transaction library.
        if recipient := self.transaction_library.get_email(self.type):
            return [recipient]

    @classmethod
    def get_notification_context(cls, notifications=None):
        """Get the context to render the notification template."""
        context = {'loans': []}
        notifications = notifications or []

        item_dumper = ItemNotificationDumper()
        patron_dumper = PatronNotificationDumper()
        for notification in notifications:
            loan = notification.loan
            creation_date = format_date_filter(
                notification.get('creation_date'), date_format='medium',
                locale=language_iso639_2to1(notification.get_language_to_use())
            )
            # merge doc and item metadata preserving document key
            item_data = notification.item.dumps(dumper=item_dumper)
            doc_data = notification.document.dumps(
                dumper=document_title_dumper)
            doc_data = {**item_data, **doc_data}
            # pickup location name --> !! pickup is on notif.request_loan, not
            # on notif.loan
            request_loan = notification.request_loan
            pickup_location = Location.get_record_by_pid(
                request_loan.get('pickup_location_pid')) or \
                Location.get_record_by_pid(
                    request_loan.get('transaction_location_pid'))
            # request_patron
            request_patron = Patron.get_record_by_pid(
                request_loan.get('patron_pid'))

            loan_context = {
                'creation_date': creation_date,
                'in_transit': loan.state in LoanState.ITEM_IN_TRANSIT,
                'document': doc_data,
                'pickup_name': pickup_location.get(
                    'pickup_name', pickup_location.get('name')),
                'patron': request_patron.dumps(dumper=patron_dumper)
            }
            context['loans'].append(loan_context)

        return context
