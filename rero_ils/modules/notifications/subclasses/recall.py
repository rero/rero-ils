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

"""API for manipulating "recall" circulation notifications."""

from __future__ import absolute_import, print_function

import ciso8601

from rero_ils.modules.documents.dumpers import document_title_dumper
from rero_ils.modules.items.models import ItemStatus
from rero_ils.modules.libraries.dumpers import \
    LibraryCirculationNotificationDumper
from rero_ils.modules.patrons.dumpers import PatronNotificationDumper

from .circulation import CirculationNotification
from ..models import NotificationChannel


class RecallCirculationNotification(CirculationNotification):
    """Recall circulation notifications class.

    A recall notification is a message send to the patron to notify that the
    borrowed documents should be returned to library.
    """

    def can_be_cancelled(self):
        """Check if a notification can be cancelled.

        A RECALL notification can be cancelled if the related item
        isn't ON_LOAN anymore.

        :return a tuple with two values: a boolean to know if the notification
                can be cancelled; the reason why the notification could be
                cancelled (only present if tuple first value is True).
        """
        # Check if parent class would cancel the notification. If yes other
        # check can be skipped.
        can, reason = super().can_be_cancelled()
        if can:
            return can, reason
        # Check if the related item is still ON_LOAN
        if self.item.status != ItemStatus.ON_LOAN:
            return True, "Item isn't anymore ON_LOAN state"
        # we don't find any reasons to cancel this notification
        return False, None

    @classmethod
    def get_notification_context(cls, notifications=None):
        """Get the context to render the notification template."""
        # RECALL notifications are always aggregated by library and by
        # patron. So we could use the first notification of the list to get
        # global information about these data. We need to loop on each
        # notification to get the documents information related to each loan.
        context = {}
        notifications = notifications or []
        if not notifications:
            return context

        patron = notifications[0].patron
        library = notifications[0].library
        include_address = notifications[0].get_communication_channel == \
            NotificationChannel.MAIL
        # Dump basic informations
        context |= {
            'include_patron_address': include_address,
            'patron': patron.dumps(dumper=PatronNotificationDumper()),
            'library': library.dumps(
                dumper=LibraryCirculationNotificationDumper()),
            'loans': []
        }
        # Add metadata for any ``notification.loan`` of the notifications list
        for notification in notifications:
            end_date = notification.loan.get('end_date')
            if end_date:
                end_date = ciso8601.parse_datetime(end_date)
                end_date = end_date.strftime("%d.%m.%Y")
            context['loans'].append({
                'document': notification.document.dumps(
                    dumper=document_title_dumper),
                'end_date': end_date
            })
        return context
