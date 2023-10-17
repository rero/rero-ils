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

"""API for manipulating "availability" circulation notifications."""

from __future__ import absolute_import, print_function

import ciso8601

from rero_ils.modules.documents.dumpers import document_title_dumper
from rero_ils.modules.items.dumpers import ItemNotificationDumper
from rero_ils.modules.libraries.dumpers import \
    LibraryCirculationNotificationDumper
from rero_ils.modules.patrons.dumpers import PatronNotificationDumper

from .circulation import CirculationNotification
from ..models import NotificationChannel, NotificationType


class AvailabilityCirculationNotification(CirculationNotification):
    """Availability circulation notifications class."""

    def can_be_cancelled(self):
        """Check if a notification can be be cancelled.

        An AVAILABILITY notification can be cancelled if the related item
        is already ON_LOAN. We need to call the loan to check all notification
        candidates and check if AVAILABILITY is into candidates.

        :return a tuple with two values: a boolean to know if the notification
                can be cancelled; the reason why the notification can be
                cancelled (only present if tuple first value is True).
        """
        # Check if parent class would cancel the notification. If yes other
        # check could be skipped.
        can, reason = super().can_be_cancelled()
        if can:
            return can, reason
        # Check loan notification candidate (by unpacking tuple's notification
        # candidate)
        candidates_types = [
            n[1] for n in
            self.loan.get_notification_candidates(trigger=None)
        ]
        if self.type not in candidates_types:
            msg = "Notification type isn't into notification candidate"
            return True, msg
        # we don't find any reasons to cancel this notification
        return False, None

    @classmethod
    def get_notification_context(cls, notifications=None):
        """Get the context to render the notification template.

        AVAILABILITY notification are always aggregated by library and by
        patron. So we could use the first notification of the list to get
        global information about these data. We need to loop on each
        notification to get the documents information and pickup location
        informations related to each loan.
        """
        context = {}
        notifications = notifications or []
        if not notifications:
            return context

        patron = notifications[0].patron
        library = notifications[0].pickup_library
        include_address = notifications[0].get_communication_channel() == \
            NotificationChannel.MAIL
        # Dump basic informations
        context |= {
            'include_patron_address': include_address,
            'patron': patron.dumps(dumper=PatronNotificationDumper()),
            'library': library.dumps(
                dumper=LibraryCirculationNotificationDumper()),
            'loans': [],
            'delay': 0
        }
        # Availability notification could be sent with a delay. We need to find
        # this delay into the library notifications settings and convert it
        # from minutes to seconds.
        for setting in library.get('notification_settings', []):
            if setting['type'] == NotificationType.AVAILABILITY:
                context['delay'] = setting.get('delay', 0)*60
        # Add metadata for any ``notification.loan`` of the notifications list
        item_dumper = ItemNotificationDumper()
        for notification in notifications:
            loc = lib = None
            keep_until = notification.loan.get('request_expire_date')
            if keep_until:
                keep_until = ciso8601.parse_datetime(keep_until)

            if notification.pickup_location:
                loc = notification.pickup_location
                lib = notification.pickup_library
            elif notification.transaction_location:
                loc = notification.transaction_location
                lib = notification.transaction_library
            # merge doc and item metadata preserving document key
            item_data = notification.item.dumps(dumper=item_dumper)
            doc_data = notification.document.dumps(
                dumper=document_title_dumper)
            doc_data = {**item_data, **doc_data}
            if loc and lib:
                context['loans'].append({
                    'document': doc_data,
                    'pickup_name': loc.get('pickup_name', lib.get('name')),
                    'pickup_until': keep_until
                })
        return context
