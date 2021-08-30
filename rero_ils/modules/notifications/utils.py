# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
# Copyright (C) 2021 UCLouvain
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

"""Utilities functions for notifications."""
from datetime import datetime, timedelta, timezone

from elasticsearch_dsl import Q

from rero_ils.modules.circ_policies.api import DUE_SOON_REMINDER_TYPE, \
    OVERDUE_REMINDER_TYPE, CircPolicy
from rero_ils.modules.libraries.api import Library
from rero_ils.modules.libraries.exceptions import LibraryNeverOpen
from rero_ils.modules.locations.api import Location
from rero_ils.modules.notifications.api import NotificationsSearch
from rero_ils.modules.notifications.models import NotificationChannel, \
    NotificationType


def get_library_metadata(pid):
    """Get library metadata for a specific pid.

    :param pid: the library pid.
    :return the library metadata.
    """
    library = Library.get_record_by_pid(pid)
    data = dict()
    for field in ['pid', 'email', 'name', 'address', 'notification_settings',
                  'communication_language', 'next_open']:
        data[field] = library.get(field)
    if not data['notification_settings']:
        data['notification_settings'] = []

    # TODO: make availability days variable (fixed to 10 days)
    keep_until = datetime.now(timezone.utc) + timedelta(days=10)
    try:
        next_open = library.next_open(keep_until)
        next_open = next_open.strftime("%d.%m.%Y")
        data['next_open'] = next_open
    except LibraryNeverOpen:
        # TODO: try to use context to translate the string
        data['next_open'] = 'never open'
    return data


def get_notification(loan, notification_type):
    """Returns specific notification from loan.

    :param loan: the parent loan.
    :param notification_type: the type of notification sent.
    """
    from .api import Notification
    results = NotificationsSearch()\
        .filter('term', loan__pid=loan.pid)\
        .filter('term', notification_type=notification_type)\
        .source().scan()
    try:
        pid = next(results).pid
        return Notification.get_record_by_pid(pid)
    except StopIteration:
        return None


def get_notifications(notification_type, processed=False, not_sent=False):
    """Returns specific notifications pids.

    :param notification_type: filter on the notification type.
    :param processed: filter on already processed notifications.
    :param not_sent: filter on not yet send notifications.
    :return a notification pid generator.
    """
    query = NotificationsSearch()\
        .filter('term', notification_type=notification_type) \
        .source('pid')
    if not not_sent:
        query = query.filter(
            'bool', must_not=[
                Q('exists', field='notification_sent'),
                Q('term', notification_sent=False)
            ]
        )
    if processed:
        query = query.filter('exists', field='process_date')
    else:
        query = query.filter(
            'bool', must_not=[Q('exists', field='process_date')])

    for hit in query.scan():
        yield hit.pid


def number_of_reminders_sent(loan, notification_type=NotificationType.OVERDUE):
    """Get the number of notifications sent for the given loan.

    :param loan: the parent loan.
    :param notification_type: the type of notification to find.
    :return notification counter.
    """
    return NotificationsSearch()\
        .filter('term', loan__pid=loan.pid)\
        .filter('term', notification_type=notification_type) \
        .source().count()


def exists_similar_notification(data):
    """Check if a similar notification already exists.

    :param data: the notification data.
    :return True if a similar notification has found, False otheriwse.
    """
    loan_pid = data.get('loan', {}).get('pid')
    notification_pid = data.get('pid')
    notification_type = data.get('notification_type')
    reminder_counter = data.get('reminder_counter', 0)

    query = NotificationsSearch()\
        .filter('term', loan__pid=loan_pid)\
        .filter('term', notification_type=notification_type)
    if notification_type in NotificationType.REMINDERS_NOTIFICATIONS:
        query = query.filter('term', reminder_counter=reminder_counter)
    if notification_pid:
        query = query.exclude('term', pid=notification_pid)

    return query.source().count() > 0


def get_communication_channel_to_use(loan, notification_data, patron):
    """Get the communication channel to use for a notification.

    :param loan: the notification parent loan.
    :param notification_data: the notification data.
    :param patron: the patron related to this notification
    :return the communication channel to use for this notification
    """
    from ..loans.utils import get_circ_policy
    notification_type = notification_data.get('notification_type')

    # Some notifications have always the same channel not depending of any
    # other settings.
    static_communication_channels = {
        NotificationType.TRANSIT_NOTICE: NotificationChannel.MAIL,
        NotificationType.BOOKING: NotificationChannel.MAIL,
        NotificationType.REQUEST: NotificationChannel.MAIL
    }
    if notification_type in static_communication_channels:
        return static_communication_channels[notification_type]

    # other notifications should use channel define into the affected patron
    # settings. But this setting could be override for OVERDUE and DUE_SOON, by
    # settings defined in the corresponding circulation policy.
    communication_channel = NotificationChannel.PATRON_SETTING
    if notification_type in [NotificationType.OVERDUE,
                             NotificationType.DUE_SOON]:
        cipo = get_circ_policy(loan)
        reminder_type = DUE_SOON_REMINDER_TYPE
        if notification_type != NotificationType.DUE_SOON:
            reminder_type = OVERDUE_REMINDER_TYPE
        reminder = cipo.get_reminder(
            reminder_type=reminder_type,
            idx=notification_data.get('reminder_counter', 0)
        )
        if reminder:
            communication_channel = reminder.get(
                'communication_channel',
                NotificationChannel.PATRON_SETTING
            )

    # return the best communication channel
    if communication_channel == NotificationChannel.PATRON_SETTING:
        communication_channel = patron['patron']['communication_channel']
    return communication_channel


def get_template_to_use(loan, notification_type, reminder_counter):
    """Get the template path to use for a notification.

    :param loan: the notification parent loan.
    :param notification_type: the notification type.
    :param reminder_counter: the reminder counter.
    """
    from ..loans.utils import get_circ_policy

    # depending of notification to send, the template to use could be static or
    # found into the related circulation policy.
    # TODO : depending of the communication channel, improve the function to
    #        get the correct template.
    static_template_mapping = {
        NotificationType.RECALL: 'email/recall',
        NotificationType.AVAILABILITY: 'email/availability',
        NotificationType.TRANSIT_NOTICE: 'email/transit_notice',
        NotificationType.BOOKING: 'email/booking',
        NotificationType.REQUEST: 'email/request'
    }
    if notification_type in static_template_mapping:
        return static_template_mapping[notification_type]

    # Find the related circulation policy and check about the template to use
    # into the defined reminders
    cipo = get_circ_policy(loan)
    reminder_type = DUE_SOON_REMINDER_TYPE
    if notification_type != NotificationType.DUE_SOON:
        reminder_type = OVERDUE_REMINDER_TYPE
    reminder = cipo.get_reminder(
        reminder_type=reminder_type,
        idx=reminder_counter
    )
    template = f'email/{notification_type}'
    if reminder:
        template = reminder.get('template')
    return template


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
        NotificationType.DUE_SOON: DUE_SOON_REMINDER_TYPE,
        NotificationType.OVERDUE: OVERDUE_REMINDER_TYPE
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
