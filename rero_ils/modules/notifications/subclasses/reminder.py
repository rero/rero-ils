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

"""API for manipulating reminder circulation notifications."""

from __future__ import absolute_import, print_function

import ciso8601
from num2words import num2words

from rero_ils.modules.circ_policies.api import DUE_SOON_REMINDER_TYPE, \
    OVERDUE_REMINDER_TYPE
from rero_ils.modules.documents.dumpers import document_title_dumper
from rero_ils.modules.libraries.dumpers import \
    LibraryCirculationNotificationDumper
from rero_ils.modules.loans.utils import get_circ_policy
from rero_ils.modules.patrons.dumpers import PatronNotificationDumper
from rero_ils.utils import language_iso639_2to1

from .circulation import CirculationNotification
from ..api import NotificationsSearch
from ..models import NotificationChannel, NotificationType
from ...items.dumpers import ItemNotificationDumper


class ReminderCirculationNotification(CirculationNotification):
    """Reminder circulation notifications class.

    A reminder notification is a message send to a patron to notify that a
    borrowed document requires its attention.

    The reminder notification set groups DUE_SOON and OVERDUE notifications.
    The settings about this notification set could are found in the
    circulation policy (CIPO) related to the loan, at this time.
    """

    @property
    def _cipo_reminder(self):
        """Get the related circulation policy reminder for this notification.

        REMINDERS notification are linked to settings defined in the
        circulation policy related to the loan. The cipo reminders may not
        exists (because the item circulation category [itty] changed, the
        patron type changed... since the notification creation.

        :return the cipo reminder related to this notifications.
        """
        if not hasattr(self, '_reminder'):
            cipo = get_circ_policy(self.loan)
            reminder_type = DUE_SOON_REMINDER_TYPE
            if self.type != NotificationType.DUE_SOON:
                reminder_type = OVERDUE_REMINDER_TYPE
            self._reminder = cipo.get_reminder(
                reminder_type=reminder_type,
                idx=self.get('context', {}).get('reminder_counter', 0)
            )
        return self._reminder

    def can_be_cancelled(self):
        """Check if a notification can be cancelled.

        A REMINDER notification should be cancelled if a similar notification
        has already been sent or if the related circulation policy doesn't
        define anymore this kind of notification.

        :return a tuple with two values: a boolean to know if the notification
                can be cancelled; the reason why the notification can be
                cancelled (only present if tuple first value is True).
        """
        # Check if parent class would cancel the notification. If yes other
        # check could be skipped.
        can, reason = super().can_be_cancelled()
        if can:
            return can, reason
        # Check if cipo reminder exists
        if not self._cipo_reminder:
            return True, 'No corresponding CIPO reminder found'
        # Check if a similar notification exists and has already been sent.
        if self._exists_similar_notification():
            return True, 'Similar notification already proceed'
        # we don't find any reasons to cancel this notification
        return False, None

    def _exists_similar_notification(self):
        """Check if a similar notification already exists.

        For reminders notification, it's possible to renew the loan. So
        we need to check if a similar notification is created AFTER the
        related `loan.transaction_date` (transaction_date is updated after
        circulation operation [checkout, extends, ...])

        :return True if a similar notification is found, False otherwise.
        """
        reminder_counter = self.get('context', {}).get('reminder_counter', 0)
        trans_date = self.loan.get('transaction_date')
        trans_date = ciso8601.parse_datetime(trans_date)
        query = NotificationsSearch() \
            .filter('term', context__loan__pid=self.loan_pid) \
            .filter('term', notification_type=self.type) \
            .filter('range', creation_date={'gt': trans_date}) \
            .filter('term', context__reminder_counter=reminder_counter)
        if self.pid:
            query = query.exclude('term', pid=self.pid)
        return query.source().count() > 0

    def get_communication_channel(self):
        """Get the communication channel to dispatch the notification."""
        # For REMINDERS notification, the communication channel to use is
        # define into the corresponding circulation policy
        if self._cipo_reminder:
            channel = self._cipo_reminder.get('communication_channel')
            # If CIPO communication channel is patron setting, the parent
            # class will return the correct value
            if channel != NotificationChannel.PATRON_SETTING:
                return channel
        return super().get_communication_channel()

    def get_template_path(self):
        """Get the template to use to render the notification."""
        if self._cipo_reminder:
            tmpl = self._cipo_reminder.get('template')
            return f'{tmpl}/{self.get_language_to_use()}.txt'
        return super().get_template_path()

    @classmethod
    def get_notification_context(cls, notifications=None):
        """Get the context to render the notification template."""
        # REMINDERS notifications are always aggregated by library and by
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
        item_dumper = ItemNotificationDumper()
        language = language_iso639_2to1(notifications[0].get_language_to_use())
        for notification in notifications:
            end_date = notification.loan.get('end_date')
            counter = notification.get('context', {})\
                .get('reminder_counter', 0)
            counter += 1
            literal_counter = num2words(counter, to='ordinal', lang=language)
            if end_date:
                end_date = ciso8601.parse_datetime(end_date)
                end_date = end_date.strftime("%d.%m.%Y")
            # merge doc and item metadata preserving document key
            item_data = notification.item.dumps(dumper=item_dumper)
            doc_data = notification.document.dumps(
                dumper=document_title_dumper)
            doc_data = {**item_data, **doc_data}
            context['loans'].append({
                'document': doc_data,
                'end_date': end_date,
                'reminder_counter': literal_counter
            })
        return context
